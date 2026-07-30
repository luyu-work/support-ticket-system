"""
Замер метрик проекта: «до» и «после» оптимизаций.

Из корня проекта:
  .\\.venv\\Scripts\\python.exe scripts\\measure_metrics.py --label baseline
  .\\.venv\\Scripts\\python.exe scripts\\measure_metrics.py --tickets 400 --profile naive --label baseline400 --skip-pytest
  .\\.venv\\Scripts\\python.exe scripts\\measure_metrics.py --tickets 400 --profile optimized --label after400 --skip-pytest
  .\\.venv\\Scripts\\python.exe scripts\\measure_metrics.py --compare --before baseline400 --after after400

Профили:
  optimized — как сейчас в продукте (кулдаун promote, список без комментариев)
  naive     — по-старому: без кулдауна, в списке все комментарии (тяжелее)

Результат: metrics/<label>.json
"""

from __future__ import annotations

import argparse
import contextlib
import json
import re
import statistics
import subprocess
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import StaticPool, create_engine, func, select
from sqlalchemy.orm import Session, selectinload, sessionmaker

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from app.core.database import DatabaseModelBase, get_database_session
from app.core.security import create_access_token, hash_plain_password
from app.main import ticket_system_application
from app.models import (
    SupportTicket,
    TicketComment,
    TicketStatus,
    UserAccount,
    UserRole,
)
from app.schemas.tickets import to_support_ticket_response
from app.services import support_ticket_service as ticket_svc

METRICS_DIR = ROOT / "metrics"
DEFAULT_SEED_TICKETS = 80
DEFAULT_BENCH_ROUNDS = 25

SEED_TICKETS = DEFAULT_SEED_TICKETS
BENCH_ROUNDS = DEFAULT_BENCH_ROUNDS
PROFILE = "optimized"

def count_source_lines() -> dict:
    groups = {
        "python_app": list((ROOT / "app").rglob("*.py")),
        "python_tests": list((ROOT / "tests").rglob("*.py")),
        "frontend_ts": [
            *list((ROOT / "frontend" / "src").rglob("*.ts")),
            *list((ROOT / "frontend" / "src").rglob("*.tsx")),
        ],
        "frontend_css": list((ROOT / "frontend" / "src").rglob("*.css")),
    }
    out: dict[str, dict[str, int]] = {}
    for name, files in groups.items():
        line_count = 0
        file_count = 0
        for path in files:
            if "node_modules" in path.parts or "__pycache__" in path.parts:
                continue
            file_count += 1
            with contextlib.suppress(OSError):
                line_count += sum(1 for _ in path.open(encoding="utf-8", errors="ignore"))
        out[name] = {"files": file_count, "lines": line_count}
    out["python_total_lines"] = {
        "files": out["python_app"]["files"] + out["python_tests"]["files"],
        "lines": out["python_app"]["lines"] + out["python_tests"]["lines"],
    }
    return out

def run_pytest() -> dict:
    started = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--tb=no"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    elapsed_ms = (time.perf_counter() - started) * 1000
    stdout = (proc.stdout or "") + (proc.stderr or "")
    passed = failed = 0
    m = re.search(r"(\d+)\s+passed", stdout)
    if m:
        passed = int(m.group(1))
    m = re.search(r"(\d+)\s+failed", stdout)
    if m:
        failed = int(m.group(1))
    return {
        "exit_code": proc.returncode,
        "duration_ms": round(elapsed_ms, 2),
        "passed": passed,
        "failed": failed,
        "summary_line": next(
            (
                line.strip()
                for line in reversed(stdout.splitlines())
                if "passed" in line or "failed" in line
            ),
            stdout.strip()[-200:],
        ),
    }

def _build_bench_session() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    DatabaseModelBase.metadata.create_all(bind=engine)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return factory()

def _seed_bench_data(session: Session) -> tuple[UserAccount, UserAccount, str, str]:
    client = UserAccount(
        email="bench.client@example.com",
        full_name="Bench Client",
        hashed_password=hash_plain_password("ClientPass123"),
        role=UserRole.CLIENT,
        is_active=True,
    )
    agent = UserAccount(
        email="bench.agent@example.com",
        full_name="Bench Agent",
        hashed_password=hash_plain_password("AgentPass123"),
        role=UserRole.AGENT,
        is_active=True,
        agent_number=99,
        work_days="[0,1,2,3,4]",
        work_time_start="09:00",
        work_time_end="18:00",
        admin_visible_password="AgentPass123",
    )
    session.add_all([client, agent])
    session.commit()
    session.refresh(client)
    session.refresh(agent)

    old_time = datetime.now(UTC) - timedelta(hours=10)
    tickets: list[SupportTicket] = []
    for i in range(SEED_TICKETS):
        tickets.append(
            SupportTicket(
                title=f"Bench {i}",
                problem_reason="other",
                description=f"bench body {i} " + ("detail " * 20),
                status=TicketStatus.IN_QUEUE if i % 2 == 0 else TicketStatus.IN_PROGRESS,
                client_author_id=client.user_account_id,
                assigned_agent_id=agent.user_account_id if i % 2 else None,
            )
        )
    session.add_all(tickets)
    session.commit()

    for ticket in tickets[::2]:
        ticket.created_at = old_time
    session.commit()

    comments: list[TicketComment] = []
    for ticket in tickets:
        for j in range(2):
            comments.append(
                TicketComment(
                    support_ticket_id=ticket.support_ticket_id,
                    author_user_id=agent.user_account_id if j == 0 else client.user_account_id,
                    comment_text=f"Bench comment {j} on ticket {ticket.support_ticket_id}",
                )
            )
    session.add_all(comments)
    session.commit()

    client_token = create_access_token(
        {"sub": str(client.user_account_id), "role": "client", "email": client.email}
    )
    agent_token = create_access_token(
        {"sub": str(agent.user_account_id), "role": "agent", "email": agent.email}
    )
    return client, agent, client_token, agent_token

def _stats(samples: list[float], *, path: str, method: str, status: int) -> dict:
    return {
        "path": path,
        "method": method,
        "status": status,
        "rounds": BENCH_ROUNDS,
        "avg_ms": round(statistics.mean(samples), 3),
        "p50_ms": round(statistics.median(samples), 3),
        "p95_ms": round(sorted(samples)[max(0, int(len(samples) * 0.95) - 1)], 3),
        "min_ms": round(min(samples), 3),
        "max_ms": round(max(samples), 3),
    }

def _bench_my_tickets_service(session: Session, client_account: UserAccount) -> dict:
    """
    Замеряет путь сериализации списка /tickets/my.

    optimized: без комментариев (как в текущем API)
    naive: грузим и сериализуем все комментарии (старое поведение)
    """
    include_comments = PROFILE == "naive"
    samples: list[float] = []

    _run_my_tickets_once(session, client_account, include_comments)

    for _ in range(BENCH_ROUNDS):
        t0 = time.perf_counter()
        _run_my_tickets_once(session, client_account, include_comments)
        samples.append((time.perf_counter() - t0) * 1000)

    return _stats(
        samples,
        path="/tickets/my",
        method="GET",
        status=200,
    )

def _run_my_tickets_once(
    session: Session,
    client_account: UserAccount,
    include_comments: bool,
) -> int:
    if include_comments:
        tickets = list(
            session.scalars(
                select(SupportTicket)
                .options(
                    selectinload(SupportTicket.attachments),
                    selectinload(SupportTicket.comments).selectinload(TicketComment.comment_author),
                )
                .where(SupportTicket.client_author_id == client_account.user_account_id)
                .order_by(SupportTicket.created_at.desc())
            ).all()
        )
        total = len(tickets)
        items = [
            to_support_ticket_response(
                ticket,
                include_activity_log=False,
                include_comments=True,
            )
            for ticket in tickets
        ]
    else:
        tickets, total = ticket_svc.list_tickets_for_client(
            session,
            client_account=client_account,
        )
        items = [
            to_support_ticket_response(
                ticket,
                include_activity_log=False,
                include_comments=False,
            )
            for ticket in tickets
        ]

    return total + len(items)

def bench_api() -> dict:
    session = _build_bench_session()

    def override_db():
        try:
            yield session
        finally:
            pass

    ticket_system_application.dependency_overrides[get_database_session] = override_db
    client_account, _agent, client_token, agent_token = _seed_bench_data(session)

    old_cooldown = ticket_svc._PROMOTE_COOLDOWN_SECONDS
    if PROFILE == "naive":
        ticket_svc._PROMOTE_COOLDOWN_SECONDS = 0.0
    else:
        ticket_svc._PROMOTE_COOLDOWN_SECONDS = 30.0
    ticket_svc.reset_promote_cooldown_for_tests()

    results: dict[str, dict] = {}
    ticket_count = 0
    comment_count = 0

    try:
        with TestClient(ticket_system_application) as http:

            def timed_http(
                name: str,
                method: str,
                path: str,
                token: str | None = None,
            ) -> None:
                headers = {"Authorization": f"Bearer {token}"} if token else {}
                samples: list[float] = []
                last_status = 0
                http.request(method, path, headers=headers)
                for _ in range(BENCH_ROUNDS):
                    t0 = time.perf_counter()
                    response = http.request(method, path, headers=headers)
                    samples.append((time.perf_counter() - t0) * 1000)
                    last_status = response.status_code
                results[name] = _stats(samples, path=path, method=method, status=last_status)

            timed_http("health", "GET", "/health")
            timed_http("pool", "GET", "/tickets/pool", agent_token)
            timed_http("archive", "GET", "/tickets/archive", agent_token)
            timed_http("problem_reasons", "GET", "/tickets/problem-reasons")

            results["my_tickets"] = _bench_my_tickets_service(session, client_account)

        ticket_count = session.scalar(select(func.count()).select_from(SupportTicket)) or 0
        comment_count = session.scalar(select(func.count()).select_from(TicketComment)) or 0
    finally:
        ticket_svc._PROMOTE_COOLDOWN_SECONDS = old_cooldown
        ticket_svc.reset_promote_cooldown_for_tests()
        ticket_system_application.dependency_overrides.clear()
        session.close()

    return {
        "seed_tickets": SEED_TICKETS,
        "ticket_count": ticket_count,
        "comment_count": comment_count,
        "profile": PROFILE,
        "bench_rounds": BENCH_ROUNDS,
        "endpoints": results,
        "notes": {
            "my_tickets": (
                "Measured list+serialize path: "
                + (
                    "WITH comments (naive)"
                    if PROFILE == "naive"
                    else "WITHOUT comments (optimized)"
                )
            ),
            "pool": (
                "Promote cooldown OFF (naive)"
                if PROFILE == "naive"
                else "Promote cooldown 30s (optimized)"
            ),
        },
    }

def collect(label: str, *, skip_pytest: bool = False) -> dict:
    print(f"\n=== Measuring metrics: {label} ===")
    print(f"    tickets={SEED_TICKETS}  rounds={BENCH_ROUNDS}  profile={PROFILE}\n")
    report = {
        "label": label,
        "measured_at": datetime.now(UTC).isoformat(),
        "tickets": SEED_TICKETS,
        "profile": PROFILE,
        "code_size": count_source_lines(),
    }
    print("1/3 code size...")
    print(json.dumps(report["code_size"], indent=2, ensure_ascii=False))

    if skip_pytest:
        print("2/3 pytest suite... SKIPPED")
        report["pytest"] = {
            "exit_code": None,
            "duration_ms": None,
            "passed": None,
            "failed": None,
            "summary_line": "skipped",
        }
    else:
        print("2/3 pytest suite...")
        report["pytest"] = run_pytest()
        print(report["pytest"]["summary_line"], f"| {report['pytest']['duration_ms']} ms")

    print("3/3 API benchmark...")
    report["api_bench"] = bench_api()
    for name, data in report["api_bench"]["endpoints"].items():
        print(
            f"  {name:16} avg={data['avg_ms']:8.2f} ms  "
            f"p95={data['p95_ms']:8.2f} ms  status={data['status']}"
        )

    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = METRICS_DIR / f"{label}.json"
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nSaved -> {out_path.relative_to(ROOT)}")
    return report

def compare(before: str = "baseline", after: str = "after") -> None:
    before_path = METRICS_DIR / f"{before}.json"
    after_path = METRICS_DIR / f"{after}.json"
    if not before_path.exists() or not after_path.exists():
        print(f"Need both metrics files: {before}.json and {after}.json")
        sys.exit(1)
    a = json.loads(before_path.read_text(encoding="utf-8"))
    b = json.loads(after_path.read_text(encoding="utf-8"))

    def delta(old: float, new: float) -> str:
        if old == 0:
            return "n/a"
        pct = ((new - old) / old) * 100
        sign = "+" if pct > 0 else ""
        return f"{sign}{pct:.1f}%"

    print(f"\n=== Comparison: {before} -> {after} ===\n")
    a_tickets = a.get("tickets") or a.get("api_bench", {}).get("seed_tickets")
    b_tickets = b.get("tickets") or b.get("api_bench", {}).get("seed_tickets")
    print(f"tickets:  {a_tickets} -> {b_tickets}")
    print(f"profile:  {a.get('profile', '?')} -> {b.get('profile', '?')}")
    if a.get("pytest", {}).get("duration_ms") and b.get("pytest", {}).get("duration_ms"):
        print(
            f"pytest:   {a['pytest']['duration_ms']} -> {b['pytest']['duration_ms']} ms  "
            f"({delta(a['pytest']['duration_ms'], b['pytest']['duration_ms'])})"
        )
    print()
    print(f"{'endpoint':16} {'before avg':>12} {'after avg':>12}  change")
    for name in a["api_bench"]["endpoints"]:
        if name not in b["api_bench"]["endpoints"]:
            continue
        old = a["api_bench"]["endpoints"][name]["avg_ms"]
        new = b["api_bench"]["endpoints"][name]["avg_ms"]
        print(f"{name:16} {old:12.2f} {new:12.2f}  {delta(old, new)}")

def main() -> None:
    global SEED_TICKETS, BENCH_ROUNDS, PROFILE

    parser = argparse.ArgumentParser(description="Measure Support Ticket System metrics")
    parser.add_argument("--label", default="baseline")
    parser.add_argument("--compare", action="store_true")
    parser.add_argument("--before", default="baseline")
    parser.add_argument("--after", default="after")
    parser.add_argument("--tickets", type=int, default=DEFAULT_SEED_TICKETS)
    parser.add_argument("--rounds", type=int, default=DEFAULT_BENCH_ROUNDS)
    parser.add_argument(
        "--profile",
        choices=("optimized", "naive"),
        default="optimized",
    )
    parser.add_argument("--skip-pytest", action="store_true")
    args = parser.parse_args()

    SEED_TICKETS = args.tickets
    BENCH_ROUNDS = args.rounds
    PROFILE = args.profile

    if args.compare:
        compare(args.before, args.after)
    else:
        collect(args.label, skip_pytest=args.skip_pytest)

if __name__ == "__main__":
    main()

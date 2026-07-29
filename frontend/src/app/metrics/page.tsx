"use client";

import { useEffect, useState } from "react";
import "../../styles/metrics.css";

type ChangeItem = {
  id: string;
  title: string;
  simple: string;
  why_faster: string;
  analogy: string;
  result: string;
  files: string[];
};

type EndpointRow = {
  key: string;
  label: string;
  what_is_it: string;
  path: string;
  baseline_avg_ms: number;
  after_avg_ms: number;
  baseline_p50_ms: number;
  after_p50_ms: number;
  baseline_p95_ms: number;
  after_p95_ms: number;
  note: string;
  verdict: string;
};

type MetricsReport = {
  title: string;
  subtitle: string;
  measured: {
    baseline_at: string;
    after_at: string;
    seed_tickets: number;
    comment_count?: number;
    bench_rounds: number;
    environment: string;
  };
  changes: ChangeItem[];
  api_endpoints: EndpointRow[];
  pytest: {
    baseline_duration_ms: number;
    after_duration_ms: number;
    passed: number;
    failed: number;
  };
  code_size: {
    baseline_app_lines: number;
    after_app_lines: number;
  };
  interview_takeaway: string[];
  how_to_read_table: string;
};

function pctChange(before: number, after: number): number {
  if (before === 0) return 0;
  return ((after - before) / before) * 100;
}

function formatMs(ms: number): string {
  return `${ms.toFixed(2)} мс`;
}

function formatPct(pct: number): string {
  const sign = pct > 0 ? "+" : "";
  return `${sign}${pct.toFixed(1)}%`;
}

function deltaClass(pct: number): string {
  if (pct <= -3) return "is-good";
  if (pct >= 8) return "is-bad";
  return "is-flat";
}

function formatWhen(iso: string): string {
  try {
    return new Date(iso).toLocaleString("ru-RU", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export default function MetricsPage() {
  const [report, setReport] = useState<MetricsReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetch("/metrics/report.json")
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json() as Promise<MetricsReport>;
      })
      .then((data) => {
        if (!cancelled) setReport(data);
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Не удалось загрузить отчёт");
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (error) {
    return (
      <div className="metrics-page">
        <p className="metrics-error">Ошибка загрузки: {error}</p>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="metrics-page">
        <p className="metrics-loading">Загружаем отчёт…</p>
      </div>
    );
  }

  const myTickets = report.api_endpoints.find((e) => e.key === "my_tickets");
  const myPct = myTickets
    ? pctChange(myTickets.baseline_avg_ms, myTickets.after_avg_ms)
    : 0;
  const linesDelta =
    report.code_size.after_app_lines - report.code_size.baseline_app_lines;

  return (
    <div className="metrics-page">
      <div className="metrics-inner">
        <header className="metrics-header">
          <div className="metrics-eyebrow">Метрики · 400 тикетов</div>
          <h1>{report.title}</h1>
          <p className="metrics-subtitle">{report.subtitle}</p>
          <div className="metrics-meta">
            <span>
              <strong>Замер «до»:</strong> {formatWhen(report.measured.baseline_at)}
            </span>
            <span>
              <strong>Замер «после»:</strong> {formatWhen(report.measured.after_at)}
            </span>
            <span>
              <strong>Тикетов:</strong> {report.measured.seed_tickets}
            </span>
            {report.measured.comment_count != null && (
              <span>
                <strong>Комментариев:</strong> {report.measured.comment_count}
              </span>
            )}
            <span>
              <strong>Повторов на ручку:</strong> {report.measured.bench_rounds}
            </span>
          </div>
          <p className="metrics-env-note">{report.measured.environment}</p>
        </header>

        <div className="metrics-cards">
          <div className="metrics-card">
            <div className="metrics-card-label">Самое понятное улучшение</div>
            <div className={`metrics-card-value ${deltaClass(myPct)}`}>
              {formatPct(myPct)}
            </div>
            <div className="metrics-card-hint">
              «Мои тикеты»:{" "}
              {myTickets
                ? `${formatMs(myTickets.baseline_avg_ms)} → ${formatMs(myTickets.after_avg_ms)}`
                : "—"}
              . Минус = быстрее.
            </div>
          </div>
          <div className="metrics-card">
            <div className="metrics-card-label">Тесты не сломались?</div>
            <div className="metrics-card-value is-good">
              {report.pytest.passed} из {report.pytest.passed + report.pytest.failed}
            </div>
            <div className="metrics-card-hint">
              Все зелёные. Время прогона suite ≈{" "}
              {(report.pytest.after_duration_ms / 1000).toFixed(0)} с.
            </div>
          </div>
          <div className="metrics-card">
            <div className="metrics-card-label">Код стал длиннее?</div>
            <div className="metrics-card-value is-neutral">
              {linesDelta >= 0 ? `+${linesDelta}` : linesDelta} строк
            </div>
            <div className="metrics-card-hint">
              В папке app: {report.code_size.baseline_app_lines} →{" "}
              {report.code_size.after_app_lines}.
            </div>
          </div>
        </div>

        <section className="metrics-section">
          <h2>Таблица: сколько ждал сервер (до → после)</h2>
          <p className="metrics-section-lead">{report.how_to_read_table}</p>
          <div className="metrics-table-wrap">
            <table className="metrics-table">
              <thead>
                <tr>
                  <th>Что это за экран</th>
                  <th className="num">Было (среднее)</th>
                  <th className="num">Стало (среднее)</th>
                  <th className="num">Разница</th>
                  <th>Вердикт</th>
                </tr>
              </thead>
              <tbody>
                {report.api_endpoints.map((row) => {
                  const pct = pctChange(row.baseline_avg_ms, row.after_avg_ms);
                  return (
                    <tr key={row.key}>
                      <td>
                        <span className="metrics-endpoint-name">{row.label}</span>
                        <span className="metrics-endpoint-path">{row.path}</span>
                        <span className="metrics-endpoint-what">{row.what_is_it}</span>
                      </td>
                      <td className="num">{formatMs(row.baseline_avg_ms)}</td>
                      <td className="num">{formatMs(row.after_avg_ms)}</td>
                      <td className="num">
                        <span className={`metrics-delta ${deltaClass(pct)}`}>
                          {formatPct(pct)}
                        </span>
                      </td>
                      <td>
                        <span className="metrics-verdict">{row.verdict}</span>
                        <span className="metrics-note-cell">{row.note}</span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <p className="metrics-section-lead metrics-section-lead-after">
            Дополнительно (медиана p50 — «типичный» запрос; p95 — почти худший случай):
          </p>
          <div className="metrics-table-wrap">
            <table className="metrics-table metrics-table-compact">
              <thead>
                <tr>
                  <th>Экран</th>
                  <th className="num">p50 было</th>
                  <th className="num">p50 стало</th>
                  <th className="num">p95 было</th>
                  <th className="num">p95 стало</th>
                </tr>
              </thead>
              <tbody>
                {report.api_endpoints.map((row) => (
                  <tr key={`${row.key}-p`}>
                    <td>{row.label}</td>
                    <td className="num">{row.baseline_p50_ms.toFixed(2)} мс</td>
                    <td className="num">{row.after_p50_ms.toFixed(2)} мс</td>
                    <td className="num">{row.baseline_p95_ms.toFixed(2)} мс</td>
                    <td className="num">{row.after_p95_ms.toFixed(2)} мс</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="metrics-section">
          <h2>Что именно поменяли в коде (простыми словами)</h2>
          <p className="metrics-section-lead">
            Четыре маленьких улучшения. У каждого: что сделали, почему быстрее, аналогия и цифры.
          </p>
          <ul className="metrics-changes">
            {report.changes.map((change) => (
              <li key={change.id} className="metrics-change">
                <p className="metrics-change-title">{change.title}</p>
                <div className="metrics-change-block">
                  <span className="metrics-change-label">Что сделали</span>
                  <p className="metrics-change-detail">{change.simple}</p>
                </div>
                <div className="metrics-change-block">
                  <span className="metrics-change-label">Почему это ускоряет</span>
                  <p className="metrics-change-detail">{change.why_faster}</p>
                </div>
                <div className="metrics-change-block">
                  <span className="metrics-change-label">Аналогия</span>
                  <p className="metrics-change-detail">{change.analogy}</p>
                </div>
                <div className="metrics-change-block">
                  <span className="metrics-change-label">Что в цифрах</span>
                  <p className="metrics-change-detail">{change.result}</p>
                </div>
                <div className="metrics-change-files">
                  {change.files.map((file) => (
                    <span key={file} className="metrics-file-chip">
                      {file}
                    </span>
                  ))}
                </div>
              </li>
            ))}
          </ul>
        </section>

        <section className="metrics-section">
          <h2>Что сказать на собеседовании (можно почти дословно)</h2>
          <p className="metrics-section-lead">
            Спокойно, честно, без воды. Лучше так, чем «мы всё оптимизировали в 100 раз».
          </p>
          <ol className="metrics-takeaways">
            {report.interview_takeaway.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ol>
        </section>

        <footer className="metrics-footer">
          <span>
            Сырые числа:{" "}
            <a href="/metrics/baseline400.json" target="_blank" rel="noreferrer">
              до
            </a>
            {" · "}
            <a href="/metrics/after400.json" target="_blank" rel="noreferrer">
              после
            </a>
            {" · "}
            <a href="/metrics/report.json" target="_blank" rel="noreferrer">
              отчёт
            </a>
          </span>
          <a href="/">← На главную</a>
        </footer>
      </div>
    </div>
  );
}

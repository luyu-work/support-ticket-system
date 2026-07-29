# Support Ticket System

Clients create support tickets. Agents pick them from a pool, comment, and close them. Admins watch the queue (MVP dashboard later).

## Stack

- FastAPI
- PostgreSQL
- SQLAlchemy + Alembic
- JWT auth (next steps)
- Docker
- pytest

## Project layout

```
app/
  main.py              # FastAPI app factory + entrypoint
  core/                # settings, database, logging
  api/                 # HTTP routes
  models/              # UserAccount, SupportTicket, comments, attachments
  schemas/             # request/response bodies (later)
alembic/               # DB migrations
tests/
docker-compose.yml
```

### Database models (v.0.2.0)

| Model | Table | Role |
|-------|--------|------|
| `UserAccount` | `user_accounts` | client / agent / admin |
| `SupportTicket` | `support_tickets` | ticket + status + reason |
| `TicketComment` | `ticket_comments` | comments on a ticket |
| `TicketAttachment` | `ticket_attachments` | photos (max 10 in app logic) |

## Quick start (local, Windows PowerShell)

Команды вводите **по одной строке**. Не копируйте несколько строк в одну.

### 1. Python env

```powershell
cd C:\Users\lubu\Desktop\PythonProject
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

В `.env` по умолчанию стоит **SQLite** (Docker не нужен):

```env
DATABASE_URL_OVERRIDE=sqlite:///./ticket_system_local.db
```

### 2. Run API (без Docker)

```powershell
.\.venv\Scripts\Activate.ps1
python start_project.py
```

Таблицы и admin/agent создадутся сами при старте.

### 3. (Опционально) PostgreSQL через Docker

Нужен [Docker Desktop](https://www.docker.com/products/docker-desktop/).  
Потом в `.env` уберите/закомментируйте `DATABASE_URL_OVERRIDE` и:

```powershell
docker compose up -d postgres
python -m alembic upgrade head
python start_project.py
```

Важно: `alembic` — через venv: `python -m alembic`, не просто `alembic`.

- API: http://127.0.0.1:8000  
- Docs: http://127.0.0.1:8000/docs  
- Health: http://127.0.0.1:8000/health  

### 4. Auth (v.0.3.0)

| Method | Path | Who |
|--------|------|-----|
| POST | `/auth/register` | new client (email, full_name, password) |
| POST | `/auth/login` | client / agent / admin |
| GET | `/auth/me` | any logged-in user (Bearer token) |

Default staff (created on API startup if missing):

| Role | Email | Password |
|------|--------|----------|
| admin | `admin@example.com` | `AdminChangeMe123` |
| agent | `agent@example.com` | `AgentChangeMe123` |

Change them in `.env` (`SEED_ADMIN_*`, `SEED_AGENT_*`).

Example register body:

```json
{
  "email": "client@example.com",
  "full_name": "Иван Иванов",
  "password": "ClientPass123"
}
```

Use `Authorization: Bearer <access_token>` for protected routes.

### 5. Tests

```bash
pytest
```

### Full stack in Docker

```bash
docker compose up --build
```

API will be on http://127.0.0.1:8000 (uses settings from `.env.example` by default).

## Versioning

Commits use `v.x.x.x` (major.minor.patch).

## Notes

- Local brief `input.md` is **not** committed (see `.gitignore`).
- Secrets live in `.env` (not in git). Copy from `.env.example`.

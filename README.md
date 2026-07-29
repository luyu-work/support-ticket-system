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

Apply migrations (PostgreSQL must be running):

```bash
docker compose up -d postgres
alembic upgrade head
```

## Quick start (local)

### 1. Python env

```bash
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
copy .env.example .env
```

### 2. PostgreSQL via Docker

```bash
docker compose up -d postgres
```

### 3. Run API

```bash
python start_project.py
```

- API: http://127.0.0.1:8000  
- Docs: http://127.0.0.1:8000/docs  
- Health: http://127.0.0.1:8000/health  

### 4. Tests

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

# Support Ticket System

Система тикетов поддержки. Клиенты создают обращения, агенты берут их из пула, комментируют и закрывают. Админ смотрит очередь (MVP dashboard — позже).

## Стек

**Backend**
- FastAPI
- PostgreSQL (или SQLite локально)
- SQLAlchemy + Alembic
- JWT
- pytest

**Frontend**
- Next.js (App Router)
- React
- TypeScript

## Структура

```
app/                 # FastAPI backend (только API)
frontend/            # Next.js UI
  src/app/           # страницы (login, register, tickets, home)
  src/components/    # React-компоненты
  src/lib/           # api client, auth storage, labels
  src/styles/        # CSS (разбитые стили auth / tickets)
alembic/
tests/
```

## Быстрый старт (Windows PowerShell)

Команды **по одной строке**.

### 1. Backend API

```powershell
cd C:\Users\lubu\Desktop\PythonProject
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python start_project.py
```

API: http://127.0.0.1:8000  
Docs: http://127.0.0.1:8000/docs  

В `.env` по умолчанию SQLite:

```env
DATABASE_URL_OVERRIDE=sqlite:///./ticket_system_local.db
```

### 2. Frontend (Next.js)

Отдельное окно терминала:

```powershell
cd C:\Users\lubu\Desktop\PythonProject\frontend
copy .env.example .env.local
npm install
npm run dev
```

UI: **http://127.0.0.1:3000**

`NEXT_PUBLIC_API_BASE_URL` в `frontend/.env.local` указывает на API (`http://127.0.0.1:8000`).

### 3. (Опционально) PostgreSQL

```powershell
docker compose up -d postgres
# в .env убрать DATABASE_URL_OVERRIDE
python -m alembic upgrade head
python start_project.py
```

## Auth

| Method | Path | Кто |
|--------|------|-----|
| `POST` | `/auth/register` | client |
| `POST` | `/auth/login` | client / agent / admin |
| `GET` | `/auth/me` | любой с JWT |

Staff (сиды при старте API):

| Role | Email | Password |
|------|--------|----------|
| admin | `root@gmail.com` | `root` |
| agent | `agent_1@gmail.com` | `agent_1` |

## Тикеты (API)

| Method | Path | Кто |
|--------|------|-----|
| `GET` | `/tickets/problem-reasons` | причины |
| `POST` | `/tickets` | client создаёт тикет |
| `GET` | `/tickets/my` | client — свои тикеты |
| `GET` | `/tickets/{id}` | detail |
| `GET` | `/tickets/{id}/attachments/{aid}/file` | фото |
| `GET` | `/tickets/pool` | общий пул (agent/admin) |
| `POST` | `/tickets/{id}/claim` | агент берёт тикет в работу |

Тикет в очереди дольше **8 часов** автоматически получает статус `important`.

## UI (Next.js)

| URL | Страница |
|-----|----------|
| `/login` | вход |
| `/register` | регистрация client |
| `/tickets` | «Мои тикеты» (client) |
| `/agent/pool` | общий пул тикетов (agent) |
| `/home` | заглушка admin |

Клиент → `/tickets`, агент → `/agent/pool`.  
Пул общий: любой свободный агент открывает незанятый тикет и забирает его (`claim`).

## Тесты backend

```powershell
.\.venv\Scripts\Activate.ps1
pytest
```

## Версионирование

Коммиты: `v.x.x.x` (major.minor.patch).

## Заметки

- `input.md` не в git
- Секреты в `.env` / `frontend/.env.local`
- SQLite `ticket_system_local.db` и `uploads/` не в git
- Старый vanilla HTML/CSS/JS удалён — UI только в `frontend/`

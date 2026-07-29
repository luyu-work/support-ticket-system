# Support Ticket System

Система тикетов поддержки. Клиенты создают обращения, агенты берут их из пула, комментируют и закрывают. **Админ управляет агентами** (создание, график, пароли, удаление).

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
  src/app/           # страницы (login, register, tickets, agent/*)
  src/components/    # React-компоненты
  src/lib/           # api client, auth storage, labels
  src/styles/        # CSS (auth / tickets / agent)
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
| `POST` | `/auth/logout` | сброс online-статуса агента |
| `GET` | `/auth/me` | любой с JWT |

Staff (сиды при старте API):

| Role | Email | Password |
|------|--------|----------|
| admin | `root@gmail.com` | `root` |
| agent (№1) | `agent_1@gmail.com` | `agent_1` |

Агенты, созданные админом, логинятся с **email и паролем**, которые задал админ (в карточке видны и редактируются).

## Роли

| Роль | Что делает |
|------|------------|
| **client** | Регистрация, создание тикетов, просмотр своих + комментарий поддержки |
| **agent** | Пул, архив, claim / close / transfer, логи тикета |
| **admin** | Список агентов: добавить, править ФИО/номер/пароль/график/время, удалить |

## Тикеты (API)

| Method | Path | Кто |
|--------|------|-----|
| `GET` | `/tickets/problem-reasons` | причины |
| `POST` | `/tickets` | client создаёт тикет |
| `GET` | `/tickets/my` | client — все свои тикеты |
| `GET` | `/tickets/{id}` | detail |
| `GET` | `/tickets/{id}/attachments/{aid}/file` | фото |
| `GET` | `/tickets/pool` | общий пул (agent), без закрытых |
| `GET` | `/tickets/archive` | архив закрытых (agent) |
| `POST` | `/tickets/{id}/claim` | агент берёт тикет в работу |
| `POST` | `/tickets/{id}/close` | агент закрывает с комментарием |
| `POST` | `/tickets/{id}/transfer-to-engineers` | передать инженерам |

Тикет в очереди дольше **8 часов** → статус `important`.  
Закрытый тикет уходит в **архив**.  
**История** тикета (логи) — только agent (кнопка «Логи»).  
Комментарий при закрытии видит клиент.

## Админ: агенты (API)

| Method | Path | Что |
|--------|------|-----|
| `GET` | `/admin/agents` | список активных агентов |
| `POST` | `/admin/agents` | создать (ФИО, номер, пароль, график, время) |
| `GET` | `/admin/agents/{id}` | карточка |
| `PATCH` | `/admin/agents/{id}` | редактировать |
| `DELETE` | `/admin/agents/{id}` | деактивировать (soft-delete) |

Поля агента: `agent_number`, `work_days` (0=Пн … 6=Вс), `work_time_start` / `work_time_end` (`HH:MM`).

## UI (Next.js)

| URL | Страница |
|-----|----------|
| `/login` | вход |
| `/register` | регистрация client |
| `/tickets` | «Мои тикеты» (client) |
| `/agent/pool` | пул тикетов (agent) |
| `/agent/archive` | архив (agent) |
| `/agent/agents` | управление агентами (admin) |

Маршруты после входа: client → `/tickets`, agent → `/agent/pool`, admin → `/agent/agents`.

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
- UI только в `frontend/`

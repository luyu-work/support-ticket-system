# Support Ticket System

Система тикетов поддержки. Клиенты создают обращения, агенты берут их из пула, комментируют и закрывают. Админ смотрит очередь (MVP dashboard — позже).

## Стек

- FastAPI
- PostgreSQL (или SQLite для локальной разработки)
- SQLAlchemy + Alembic
- JWT
- Docker (опционально)
- pytest

## Структура проекта

```
app/
  main.py              # factory приложения FastAPI + entrypoint
  core/                # settings, database, logging
  api/                 # HTTP-роуты
  models/              # UserAccount, SupportTicket, comments, attachments
  schemas/             # тела request/response
  services/            # бизнес-логика
  web/                 # HTML-страницы и static (CSS/JS)
alembic/               # миграции БД
tests/
docker-compose.yml
start_project.py       # локальный запуск API
```

### Модели БД

| Model | Table | Назначение |
|-------|--------|------------|
| `UserAccount` | `user_accounts` | client / agent / admin |
| `SupportTicket` | `support_tickets` | тикет, статус, причина |
| `TicketComment` | `ticket_comments` | комментарии к тикету |
| `TicketAttachment` | `ticket_attachments` | фото (до 10 на тикет — в логике приложения) |

## Быстрый старт (Windows PowerShell)

Команды вводите **по одной строке**. Не копируйте несколько строк в одну.

### 1. Окружение Python

```powershell
cd C:\Users\lubu\Desktop\PythonProject
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

В `.env` по умолчанию используется **SQLite** (Docker не нужен):

```env
DATABASE_URL_OVERRIDE=sqlite:///./ticket_system_local.db
```

### 2. Запуск API (без Docker)

```powershell
.\.venv\Scripts\Activate.ps1
python start_project.py
```

Таблицы и учётки admin/agent создаются при старте (если их ещё нет).

Полезные адреса:

- UI вход: http://127.0.0.1:8000/login  
- API: http://127.0.0.1:8000  
- Docs: http://127.0.0.1:8000/docs  
- Health: http://127.0.0.1:8000/health  

### 3. (Опционально) PostgreSQL через Docker

Нужен [Docker Desktop](https://www.docker.com/products/docker-desktop/).  
В `.env` уберите или закомментируйте `DATABASE_URL_OVERRIDE`, затем:

```powershell
docker compose up -d postgres
python -m alembic upgrade head
python start_project.py
```

Важно: Alembic запускайте через venv: `python -m alembic`, а не просто `alembic`.

### 4. Auth

| Method | Path | Кто |
|--------|------|-----|
| `POST` | `/auth/register` | новый client (`email`, `full_name`, `password`) |
| `POST` | `/auth/login` | client / agent / admin |
| `GET` | `/auth/me` | любой авторизованный пользователь (`Bearer` token) |

**Staff по умолчанию** (создаётся при старте API, если записи с таким email ещё нет):

| Role | Email | Password |
|------|--------|----------|
| admin | `root@gmail.com` | `root` |
| agent | `agent_1@gmail.com` | `agent_1` |

Сменить можно в `.env` (`SEED_ADMIN_*`, `SEED_AGENT_*`).

Пример тела для `POST /auth/register`:

```json
{
  "email": "client@example.com",
  "full_name": "Иван Иванов",
  "password": "ClientPass123"
}
```

Для защищённых эндпоинтов:

```http
Authorization: Bearer <access_token>
```

### Страницы UI

| URL | Страница |
|-----|----------|
| `/` | редирект → `/login` |
| `/login` | форма входа |
| `/register` | регистрация client |
| `/tickets` | «Мои тикеты» (client) |
| `/tickets/new` | «Обратная связь» — создание тикета |
| `/home` | заглушка (agent / admin) |

После `python start_project.py` откройте: http://127.0.0.1:8000/login  
Клиент после входа/регистрации попадает на `/tickets`.

### Тикеты (v.0.5.0)

| Method | Path | Кто |
|--------|------|-----|
| `GET` | `/tickets/problem-reasons` | список причин для select |
| `POST` | `/tickets` | client создаёт тикет (`multipart`: `problem_reason`, `description`, optional `photos`) |
| `GET` | `/tickets/my` | client — свои тикеты |
| `GET` | `/tickets/{id}` | client (свои) / agent / admin |

Статус нового тикета: `in_queue`. Фото — до 10 шт., папка `uploads/` (не в git).

### 5. Тесты

```powershell
pytest
```

### Полный стек в Docker

```powershell
docker compose up --build
```

API будет на http://127.0.0.1:8000 (настройки из `.env.example`, если не переопределены).

## Версионирование

Коммиты в формате `v.x.x.x` (major.minor.patch).

## Заметки

- Локальное ТЗ `input.md` **не** коммитится (см. `.gitignore`).
- Секреты хранятся в `.env` (не в git). Образец — `.env.example`.
- Локальный файл SQLite `ticket_system_local.db` тоже не в git.

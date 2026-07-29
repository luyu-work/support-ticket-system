# Support Ticket System

Система обращений в поддержку: клиенты создают тикеты, агенты разбирают пул, админ управляет агентами.

| | |
|---|---|
| **Backend** | FastAPI · SQLAlchemy · Alembic · JWT · pytest |
| **Frontend** | Next.js (App Router) · React · TypeScript |
| **БД** | PostgreSQL (Docker) или SQLite локально |
| **Версия** | `v.1.0.0` |

---

## Возможности

- **Клиент** — регистрация, создание тикетов (фото до 5 шт.), список «Мои тикеты», просмотр комментария поддержки
- **Агент** — общий пул, claim / close / transfer, архив, логи активности тикета
- **Админ** — CRUD агентов: ФИО, номер, email, пароль, график и время работы
- **Правила** — тикет в очереди дольше 8 ч → статус `important`; закрытый → архив
- **Метрики** — страница `/metrics` и скрипт замеров «до / после» оптимизации

---

## Стек

```
┌─────────────┐     JWT      ┌──────────────┐     SQL      ┌────────────┐
│  Next.js    │ ───────────► │   FastAPI    │ ───────────► │ PostgreSQL │
│  :3000      │ ◄─────────── │   :8000      │ ◄─────────── │  / SQLite  │
└─────────────┘   JSON API   └──────────────┘              └────────────┘
```

| Слой | Технологии |
|------|------------|
| API | FastAPI, Pydantic, python-jose (JWT), bcrypt |
| ORM / миграции | SQLAlchemy 2.x, Alembic |
| UI | Next.js App Router, CSS-токены (`globals.css`) |
| Тесты | pytest + TestClient |
| Инфра | Docker Compose (Postgres), Dockerfile |

---

## Структура репозитория

```
app/                     # FastAPI: api, models, services, schemas, core
frontend/                # Next.js UI
  src/app/               # страницы (login, tickets, agent/*, metrics)
  src/components/        # React-компоненты
  src/lib/               # api client, auth, labels
  src/styles/            # auth / tickets / agent / metrics
alembic/                 # миграции БД
tests/                   # pytest (~50 тестов)
scripts/measure_metrics.py
metrics/                 # JSON-снимки замеров (baseline400 / after400)
docker-compose.yml
start_project.py
```

---

## Быстрый старт (Windows PowerShell)

Команды — **по одной строке**.

### 1. Backend

```powershell
cd C:\Users\lubu\Desktop\PythonProject
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python start_project.py
```

| | URL |
|---|-----|
| API | http://127.0.0.1:8000 |
| Swagger | http://127.0.0.1:8000/docs |
| Health | http://127.0.0.1:8000/health |

В `.env` по умолчанию SQLite:

```env
DATABASE_URL_OVERRIDE=sqlite:///./ticket_system_local.db
```

### 2. Frontend

Отдельное окно терминала:

```powershell
cd C:\Users\lubu\Desktop\PythonProject\frontend
copy .env.example .env.local
npm install
npm run dev
```

UI: **http://127.0.0.1:3000**

В `frontend/.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

### 3. PostgreSQL (опционально)

```powershell
docker compose up -d postgres
# в .env закомментировать DATABASE_URL_OVERRIDE
python -m alembic upgrade head
python start_project.py
```

---

## Учётки (seed при старте API)

| Роль | Email | Пароль |
|------|--------|--------|
| admin | `root@gmail.com` | `root` |
| agent №1 | `agent_1@gmail.com` | `agent_1` |

Агентов, созданных админом, логинят с **email и паролем**, заданными в карточке агента.

---

## Роли

| Роль | UI после входа | Возможности |
|------|----------------|-------------|
| **client** | `/tickets` | Создать тикет, смотреть свои, комментарий поддержки |
| **agent** | `/agent/pool` | Пул, архив, взять / закрыть / передать, логи |
| **admin** | `/agent/agents` | Список агентов: создать, править, удалить (soft) |

---

## UI

| URL | Кто | Описание |
|-----|-----|----------|
| `/login` | все | Вход |
| `/register` | client | Регистрация |
| `/tickets` | client | Мои тикеты |
| `/agent/pool` | agent | Пул |
| `/agent/archive` | agent | Архив |
| `/agent/agents` | admin | Управление агентами |
| `/metrics` | публично | Отчёт «до / после» оптимизации (400 тикетов) |

---

## API (кратко)

### Auth

| Method | Path | Описание |
|--------|------|----------|
| `POST` | `/auth/register` | Регистрация client |
| `POST` | `/auth/login` | JWT |
| `POST` | `/auth/logout` | Сброс online-статуса агента |
| `GET` | `/auth/me` | Текущий пользователь |

### Тикеты

| Method | Path | Кто |
|--------|------|-----|
| `GET` | `/tickets/problem-reasons` | причины (справочник) |
| `POST` | `/tickets` | client создаёт тикет (multipart) |
| `GET` | `/tickets/my` | client — список **без** комментариев |
| `GET` | `/tickets/{id}` | detail (+ comments, activity для staff) |
| `GET` | `/tickets/{id}/attachments/{aid}/file` | файл фото |
| `GET` | `/tickets/pool` | agent — пул (без closed) |
| `GET` | `/tickets/archive` | agent — архив |
| `POST` | `/tickets/{id}/claim` | взять в работу |
| `POST` | `/tickets/{id}/close` | закрыть **с комментарием** |
| `POST` | `/tickets/{id}/transfer-to-engineers` | передать инженерам |

### Админ: агенты

| Method | Path | Описание |
|--------|------|----------|
| `GET` | `/admin/agents` | список |
| `POST` | `/admin/agents` | создать |
| `GET` | `/admin/agents/{id}` | карточка |
| `PATCH` | `/admin/agents/{id}` | править |
| `DELETE` | `/admin/agents/{id}` | деактивировать |

Поля агента: `agent_number`, `work_days` (0=Пн … 6=Вс), `work_time_start` / `work_time_end` (`HH:MM`), email, пароль (виден админу).

Полный контракт: **http://127.0.0.1:8000/docs**

---

## Бизнес-правила

1. Тикет в очереди дольше **8 часов** → статус `important` (bulk UPDATE + cooldown 30 с).
2. Закрытый тикет уходит в **архив**.
3. **Логи** активности — только agent/admin.
4. Комментарий при закрытии видит **клиент**.
5. Список `/tickets/my` не отдаёт комментарии (они в detail) — меньше payload.

---

## Метрики и оптимизация

Страница в UI: **http://127.0.0.1:3000/metrics**

Замер на **400 тикетах** (+ 800 комментариев), 25 раундов, сравнение naive vs optimized:

| Экран | До | После | Δ |
|-------|-----|-------|---|
| Мои тикеты | ~40.8 мс | ~12.1 мс | **−70%** |
| Пул / архив | ~13 / ~3 мс | близко | шум / не цель |

Что ускорили:

1. Список «мои тикеты» **без** комментариев  
2. Cooldown 30 с на promote «важное»  
3. Bulk UPDATE статусов important  
4. Кэш справочника problem-reasons  

Перезапуск замера:

```powershell
.\.venv\Scripts\Activate.ps1
python scripts\measure_metrics.py --tickets 400 --profile naive --label baseline400 --skip-pytest
python scripts\measure_metrics.py --tickets 400 --profile optimized --label after400 --skip-pytest
python scripts\measure_metrics.py --compare --before baseline400 --after after400
```

Снимки: `metrics/baseline400.json`, `metrics/after400.json`, `metrics/report.json`.

---

## Тесты

```powershell
.\.venv\Scripts\Activate.ps1
pytest
```

Ожидается **50 passed**. Покрыты auth, тикеты, пул/архив, админ-агенты, модели, health.

---

## Версионирование

Коммиты: `v.x.x.x` (+ короткий комментарий по смыслу).

---

## Заметки

- `input.md` **не** в git  
- Секреты только в `.env` / `frontend/.env.local`  
- `ticket_system_local.db`, `uploads/` — локальные, в git не коммитятся  
- UI только в `frontend/` (бэкенд — API-only)

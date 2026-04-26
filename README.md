# Internal Reporting System

REST API для управления командами, проектами, учёта рабочего времени и аналитики.
Реализован на **FastAPI + SQLAlchemy + SQLite**.

**Автор:** Александр Козлов

---

## Установка и запуск

```bash
# 1. Установить зависимости
pip install -r requirements.txt

# или через uv
uv sync

# 2. Заполнить БД тестовыми данными (пароль тестовых пользователей: dev123!)
python seed.py

# 3. Запустить сервер
uvicorn app.main:app --reload
```

Документация (Swagger UI): http://127.0.0.1:8000/docs  
ReDoc:                      http://127.0.0.1:8000/redoc

---

## Запуск тестов

```bash
pytest tests/ -v
```

74 теста, покрывающих аутентификацию, CRUD и аналитику.

---

## Структура проекта

```
report_system/
├── app/
│   ├── main.py              # Точка входа FastAPI
│   ├── database.py          # Подключение к SQLite, get_db
│   ├── auth.py              # JWT, хэширование паролей, get_current_user
│   ├── crud.py              # CRUD-операции для всех сущностей
│   ├── models/
│   │   └── __init__.py      # SQLAlchemy модели (7 таблиц)
│   ├── schemas/
│   │   └── __init__.py      # Pydantic схемы (In / Out)
│   ├── routers/
│   │   ├── auth.py          # POST /auth/register, /auth/token
│   │   ├── users.py         # /users
│   │   ├── teams.py         # /teams
│   │   ├── projects.py      # /projects
│   │   ├── reports.py       # /reports
│   │   ├── issues.py        # /issues
│   │   └── analytics.py     # /projects/{id}/dashboard, /sync/...
│   └── services/
│       └── analytics.py     # Вся бизнес-логика и алгоритмы
├── tests/
│   ├── conftest.py          # Фикстуры (in-memory БД, TestClient, auth)
│   ├── test_auth.py
│   ├── test_users.py
│   ├── test_teams.py
│   ├── test_projects.py
│   ├── test_reports.py
│   ├── test_issues.py
│   └── test_analytics.py
├── seed.py                  # Тестовые данные (3 команды, 13 пользователей)
├── requirements.txt         # Зависимости
├── pyproject.toml           # Метаданные и зависимости проекта
└── README.md
```

---

## Схема БД

```
users ────────────────────────────────┐
  id, name, email, password_hash,     │
  role, created_at                    │
  │                              (assignee)
  │ (via team_members)                │
  ▼                                   │
teams ◄──── team_members              │
  id, name, lead_id                   │
  │                                   │
  │ (via project_members)             │
  ▼                                   ▼
projects ◄──── project_members    issues
  id, name, team_id,                id, project_id, assignee_id,
  deadline, budget_hours, status    title, status, issue_type,
  │                                 priority, story_points,
  └──────────────► reports          external_id, external_source,
                   id, user_id,     closed_at, updated_at
                   project_id,
                   report_date,
                   hours_spent,
                   category
```

---

## Аутентификация

API использует JWT Bearer-токены. Запись операции (POST / PATCH / DELETE) требует авторизации.

### 1. Зарегистрироваться

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name": "Иван Иванов", "email": "ivan@corp.io", "password": "secret123", "role": "developer"}'
```

### 2. Получить токен

```bash
curl -X POST http://localhost:8000/auth/token \
  -F "username=ivan@corp.io" \
  -F "password=secret123"
# → {"access_token": "eyJ...", "token_type": "bearer"}
```

### 3. Использовать токен

```bash
TOKEN="eyJ..."
curl -X POST http://localhost:8000/projects/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "My Project", "budget_hours": 200}'
```

> В Swagger UI нажмите кнопку **Authorize** и вставьте токен — все защищённые эндпоинты будут доступны.

---

## Эндпоинты

Знак `🔒` означает, что эндпоинт требует Bearer-токен.

### Auth

| Метод | URL             | Описание                              |
|-------|-----------------|---------------------------------------|
| POST  | /auth/register  | Регистрация нового пользователя       |
| POST  | /auth/token     | Вход в систему, возвращает JWT-токен  |

### Команды (Teams)

| Метод  | URL                           | Доступ | Описание             |
|--------|-------------------------------|--------|----------------------|
| GET    | /teams/                       |        | Список команд        |
| POST   | /teams/                       | 🔒     | Создать команду      |
| GET    | /teams/{id}                   |        | Получить по ID       |
| PATCH  | /teams/{id}                   | 🔒     | Обновить             |
| DELETE | /teams/{id}                   | 🔒     | Удалить              |
| POST   | /teams/{id}/members           | 🔒     | Добавить участника   |
| DELETE | /teams/{id}/members/{user_id} | 🔒     | Убрать участника     |

### Пользователи (Users)

| Метод  | URL           | Доступ | Описание               |
|--------|---------------|--------|------------------------|
| GET    | /users/       |        | Список пользователей   |
| POST   | /users/       | 🔒     | Создать пользователя   |
| GET    | /users/{id}   |        | Получить по ID         |
| PATCH  | /users/{id}   | 🔒     | Обновить               |
| DELETE | /users/{id}   | 🔒     | Удалить                |

### Проекты (Projects)

| Метод  | URL                              | Доступ | Описание             |
|--------|----------------------------------|--------|----------------------|
| GET    | /projects/                       |        | Список проектов      |
| POST   | /projects/                       | 🔒     | Создать проект       |
| GET    | /projects/{id}                   |        | Получить по ID       |
| PATCH  | /projects/{id}                   | 🔒     | Обновить             |
| DELETE | /projects/{id}                   | 🔒     | Удалить              |
| GET    | /projects/{id}/members           |        | Участники проекта    |
| POST   | /projects/{id}/members           | 🔒     | Добавить участника   |
| DELETE | /projects/{id}/members/{user_id} | 🔒     | Убрать участника     |

Фильтр списка: `?status=active|completed|on_hold`

### Отчёты (Reports)

| Метод  | URL            | Доступ | Описание          |
|--------|----------------|--------|-------------------|
| GET    | /reports/      |        | Список с фильтрами|
| POST   | /reports/      | 🔒     | Подать отчёт      |
| GET    | /reports/{id}  |        | Получить по ID    |
| PATCH  | /reports/{id}  | 🔒     | Обновить          |
| DELETE | /reports/{id}  | 🔒     | Удалить           |

Фильтры: `project_id`, `user_id`, `date_from`, `date_to`

### Задачи (Issues)

| Метод  | URL            | Доступ | Описание                                        |
|--------|----------------|--------|-------------------------------------------------|
| GET    | /issues/       |        | Список с фильтрами                              |
| POST   | /issues/       | 🔒     | Создать задачу                                  |
| GET    | /issues/{id}   |        | Получить по ID                                  |
| PATCH  | /issues/{id}   | 🔒     | Обновить (статус `closed` авто-ставит `closed_at`) |
| DELETE | /issues/{id}   | 🔒     | Удалить                                         |

Фильтры: `project_id`, `assignee_id`, `status`, `issue_type`, `priority`

### Аналитика (Analytics)

| Метод | URL                               | Доступ | Описание                        |
|-------|-----------------------------------|--------|---------------------------------|
| GET   | /projects/{id}/dashboard          |        | Полный дашборд проекта          |
| GET   | /projects/{id}/progress           |        | Прогресс и прогноз завершения   |
| GET   | /projects/{id}/velocity?weeks=6   |        | Скорость выполнения по неделям  |
| GET   | /projects/{id}/stale-issues?stale_days=5 |   | Зависшие задачи          |
| GET   | /users/{id}/workload              |        | Загруженность сотрудника        |
| POST  | /projects/{id}/sync/gitlab        | 🔒     | Синхронизация issues из GitLab  |
| POST  | /projects/{id}/sync/jira          | 🔒     | Синхронизация issues из Jira    |

---

## Бизнес-логика (алгоритмы)

### 1. Прогноз даты завершения проекта
Рассчитывается средняя скорость выполнения (закрытых задач в неделю) за последние 6 недель.  
Прогноз: `сейчас + (open_issues / avg_velocity)`.  
Флаг `on_track = True`, если прогноз ≤ дедлайн.

### 2. Скорость выполнения по неделям
Разбивка последних N недель (по умолчанию 6) на окна Пн–Вс.  
Для каждого окна: кол-во закрытых задач + сумма story points.  
Используется для построения диаграмм сгорания задач.

### 3. Детектор перегрузки сотрудника
Суммируем часы из отчётов за последние 7 дней.  
Если сумма > 40 часов — флаг `at_risk = True` с объяснением.  
Дополнительно возвращается кол-во открытых задач.

### 4. Поиск зависших задач
Issues в статусе `in_progress` или `review`, у которых `updated_at`  
старше N дней (по умолчанию 5). Сортировка по "запущенности".

### 5. Синхронизация с GitLab / Jira
Принимает список задач в формате вебхука.  
Вставка или обновление по `external_id + external_source`.  
Маппинг статусов: GitLab `closed` → `closed`, Jira `Done` → `closed` и т.д.

---

## Примеры запросов

### Подать отчёт

```bash
curl -X POST http://localhost:8000/reports/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 3, "project_id": 1,
    "report_date": "2026-04-30",
    "hours_spent": 7.5,
    "category": "dev",
    "comment": "Implemented rate limiting"
  }'
```

### Дашборд проекта

```bash
curl http://localhost:8000/projects/1/dashboard
```

### Синхронизация issues из GitLab

```bash
curl -X POST http://localhost:8000/projects/1/sync/gitlab \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 1,
    "issues": [
      {"id": 42, "title": "Fix null pointer", "state": "opened", "labels": []},
      {"id": 43, "title": "Add auth middleware", "state": "closed", "labels": []}
    ]
  }'
```

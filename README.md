# calendar

Фронтенд на Vite + React, бэкенд на FastAPI и API-контракт на TypeSpec.

## Структура

- `frontend/` - приложение React/Vite.
- `backend/` - приложение FastAPI с SQLAlchemy, Alembic и SQLite.
- `spec/` - TypeSpec-контракт, из которого компилируется OpenAPI.

## Команды

```sh
make install
make db-reset
make dev
```

Полезные цели:

- `make dev-web` - запустить только фронтенд на `127.0.0.1:5173`.
- `make dev-api` - запустить только FastAPI-бэкенд на `127.0.0.1:8000`.
- `make db-migrate` - применить миграции Alembic.
- `make db-seed` - наполнить локальную SQLite-базу начальными данными.
- `make typespec-compile` - скомпилировать `spec/` в OpenAPI.
- `make docs PORT=8080` - поднять локальную API-документацию.
- `make test` - скомпилировать TypeSpec, запустить тесты бэкенда и собрать фронтенд.

Демо-логин из seed-данных:

- Email: `demo@example.com`
- Password: `demo`

## Деплой через Docker

Приложение упаковано в два образа: `backend` (FastAPI + uvicorn, миграции Alembic применяются при старте) и `frontend` (Vite-сборка, отдаётся через nginx, который проксирует `/api` на backend). Оркестрация — через `docker-compose.yml`.

### Быстрый старт

```sh
cp .env.example .env
# отредактируйте .env: как минимум задайте CALENDAR_JWT_SECRET
# сгенерировать секрет: openssl rand -hex 32

docker compose up -d --build
```

Приложение будет доступно на `http://<host>:8080` (порт настраивается через `WEB_PORT`). Первый деплой можно наполнить демо-данными, выставив `CALENDAR_SEED_ON_START=true` в `.env` (учтите: seed очищает таблицы).

### Управление

```sh
docker compose logs -f          # логи
docker compose ps               # статус сервисов
docker compose down             # остановить
docker compose up -d --build    # пересобрать и обновить
```

### Данные

По умолчанию используется SQLite в docker volume `calendar-data` (`/app/data/calendar.sqlite`), данные переживают перезапуск контейнеров. Для внешней БД задайте `CALENDAR_DATABASE_URL` в `.env`.

### Переменные окружения

Все переменные и значения по умолчанию описаны в `.env.example`. Ключевые: `CALENDAR_JWT_SECRET` (обязательна), `WEB_PORT`, `CALENDAR_DATABASE_URL`, `CALENDAR_CORS_ORIGINS`, `VITE_API_URL`.

## Booking events (уведомления)

Application-слой бронирований эмитит события жизненного цикла (`created`, `confirmed`, `declined`, `cancelled`) через `backend/app/application/events.py`. По умолчанию используется `LoggingBookingNotifier`, который ничего не отправляет наружу и только пишет в лог — это безопасно для local/dev.

Событие (`BookingEvent`) содержит минимальные данные для будущих уведомлений: `booking_uid`, `event_type_id`, `event_type_title`, хост (`host_username`, `host_email`), участник (`attendee_name`, `attendee_email`), `start`, `end`, `status` и `reason` (если есть).

Чтобы подключить реальный notifier (SMTP, календарный провайдер, вебхук) позже:

1. Реализуйте класс с методом `notify(self, event: BookingEvent) -> None`, удовлетворяющий протоколу `BookingNotifier`.
2. Зарегистрируйте его на старте приложения через `set_booking_notifier(MyNotifier())` (например, в `backend/app/main.py`).

Ошибки notifier перехватываются и логируются, чтобы не ломать основной booking flow.

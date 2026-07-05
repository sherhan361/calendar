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

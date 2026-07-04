# calendar

Vite + React frontend, FastAPI backend, and TypeSpec API contract.

## Structure

- `frontend/` - React/Vite application.
- `backend/` - FastAPI application with SQLAlchemy, Alembic, and SQLite.
- `spec/` - TypeSpec contract used to compile OpenAPI.

## Commands

```sh
make install
make db-reset
make dev
```

Useful targets:

- `make dev-web` - run only the frontend on `127.0.0.1:5173`.
- `make dev-api` - run only the FastAPI backend on `127.0.0.1:8000`.
- `make db-migrate` - apply Alembic migrations.
- `make db-seed` - seed the local SQLite database.
- `make typespec-compile` - compile `spec/` into OpenAPI output.
- `make docs PORT=8080` - serve local API docs.
- `make test` - compile TypeSpec, run backend tests, and build the frontend.

Seeded demo login:

- Email: `demo@example.com`
- Password: `demo`

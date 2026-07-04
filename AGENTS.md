# Repository Guidelines

## Project Structure & Module Organization

Calendar app with a Vite + React + TypeScript frontend, FastAPI backend, SQLite database, and TypeSpec API contract.

- `frontend/src/app/`: app shell, routing, and workspace state.
- `frontend/src/features/`: domain UI flows for event types, availability, bookings, auth, and public booking.
- `frontend/src/components/ui/`: reusable UI primitives.
- `frontend/src/lib/`: shared API, types, date/time, i18n, and utilities.
- `backend/app/`: FastAPI application, routes, services, schemas, config, and database setup.
- `backend/alembic/`: database migrations.
- `backend/scripts/`: local backend/dev helpers and seed data.
- `spec/`: TypeSpec API models and routes.

## Build, Test, and Development Commands

- `make install`: install frontend npm dependencies and backend Python dependencies.
- `make dev`: run FastAPI backend and Vite frontend together.
- `make dev-web`: run only the frontend on `127.0.0.1:5173`.
- `make dev-api`: run only the FastAPI backend on `127.0.0.1:8000`.
- `make db-reset`: recreate and seed the local SQLite database.
- `make db-migrate`: apply Alembic migrations.
- `make db-seed`: seed the local SQLite database.
- `make typespec-compile`: compile `spec/` to OpenAPI output in `/tmp/calendar-typespec-output`.
- `make docs PORT=8080`: serve local API docs.
- `make build`: run TypeScript and Vite production builds.
- `make test`: run TypeSpec compile, backend tests, and frontend build.

## Coding Style & Naming Conventions

Use strict TypeScript and React function components in the frontend. Keep component files in `PascalCase.tsx`, hooks in `useCamelCase.ts`, and shared helpers in `camelCase.ts`. Follow the existing style: 2-space indentation, double quotes, semicolons, named exports, and `type` aliases for props and API shapes.

Keep frontend API calls centralized in `frontend/src/lib/api.ts`, shared DTOs in `frontend/src/lib/types.ts`, and user-facing text in `frontend/src/lib/i18n.ts`. Keep backend request/response DTOs aligned with `spec/` in `backend/app/schemas/`.

## Testing Guidelines

Treat `make test` as required verification before opening a PR. For UI changes, also run `make dev` and manually verify the affected flow. Keep backend tests under `backend/tests/` and test names tied to the route, feature, or helper under test.

## Commit & Pull Request Guidelines

History is short and uses concise subjects such as `Initial commit` and `создана спека и фронт`. Use a short imperative subject in Russian or English, and keep one logical change per commit.

Pull requests should include a brief summary, verification commands, linked issue or task when available, and screenshots for visible UI changes. Call out API contract, TypeSpec, Alembic migration, or seed data changes explicitly.

## Security & Configuration Tips

The frontend reads `VITE_API_URL` and falls back to `http://127.0.0.1:8000`. The backend reads `CALENDAR_DATABASE_URL`, `CALENDAR_JWT_SECRET`, and `CALENDAR_CORS_ORIGINS`. Do not commit local secrets or generated SQLite files. Use seeded data instead of hardcoding temporary credentials.

# Repository Guidelines

## Project Structure & Module Organization

Vite + React + TypeScript calendar app with a Prisma-backed mock API.

- `src/app/`: app shell, routing, and workspace state.
- `src/features/`: domain UI flows for event types, availability, bookings, auth, and public booking.
- `src/components/ui/`: reusable UI primitives.
- `src/lib/`: shared API, types, date/time, i18n, and utilities.
- `spec/`: TypeSpec API models and routes.
- `scripts/`: local dev, mock API, database setup, and docs helpers.
- `prisma/`: SQLite schema and seed data.

## Build, Test, and Development Commands

- `npm install`: install dependencies from `package-lock.json`.
- `make dev`: run mock API and Vite frontend together.
- `make dev-web`: run only the frontend on `127.0.0.1:5173`.
- `make mock-api`: run only the Prisma-backed mock API.
- `make db-reset`: recreate and seed the local SQLite database.
- `make typespec-compile`: compile `spec/` to OpenAPI output in `/tmp/calendar-typespec-output`.
- `make docs PORT=8080`: serve local API docs.
- `make build`: run TypeScript and Vite production builds.
- `make test`: run the current smoke pipeline, TypeSpec compile plus frontend build.

## Coding Style & Naming Conventions

Use strict TypeScript and React function components. Keep component files in `PascalCase.tsx`, hooks in `useCamelCase.ts`, and shared helpers in `camelCase.ts`. Follow the existing style: 2-space indentation, double quotes, semicolons, named exports, and `type` aliases for props and API shapes.

Keep API calls centralized in `src/lib/api.ts`, shared DTOs in `src/lib/types.ts`, and user-facing text in `src/lib/i18n.ts`.

## Testing Guidelines

There is no unit test runner or coverage threshold configured yet. Treat `make test` as required verification before opening a PR. For UI changes, also run `make dev` and manually verify the affected flow. If adding a test framework, document the command here and keep test names tied to the feature or helper under test.

## Commit & Pull Request Guidelines

History is short and uses concise subjects such as `Initial commit` and `создана спека и фронт`. Use a short imperative subject in Russian or English, and keep one logical change per commit.

Pull requests should include a brief summary, verification commands, linked issue or task when available, and screenshots for visible UI changes. Call out API contract, TypeSpec, Prisma schema, or mock data changes explicitly.

## Security & Configuration Tips

The frontend reads `VITE_API_URL` and falls back to `http://127.0.0.1:8000`. Do not commit local secrets or generated SQLite files. Use seeded mock data instead of hardcoding temporary credentials.

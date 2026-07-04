NPM ?= npm
PORT ?= 8080

.DEFAULT_GOAL := help

.PHONY: help dev dev-web mock-api db-push db-seed db-reset typespec-compile compile docs build test

help:
	@printf "Available targets:\n"
	@printf "  make dev               Run mock API and Vite frontend\n"
	@printf "  make dev-web           Run Vite frontend only\n"
	@printf "  make mock-api          Run Prisma-backed mock API only\n"
	@printf "  make db-reset          Reset and seed mock SQLite DB\n"
	@printf "  make typespec-compile  Compile TypeSpec/OpenAPI\n"
	@printf "  make compile           Alias for typespec-compile\n"
	@printf "  make docs [PORT=8080]  Serve local API docs\n"
	@printf "  make build             Build frontend\n"
	@printf "  make test              Run npm test\n"

dev:
	$(NPM) run dev

dev-web:
	$(NPM) run dev:web

mock-api:
	$(NPM) run mock:api

db-push:
	$(NPM) run mock:db:push

db-seed:
	$(NPM) run mock:db:seed

db-reset:
	$(NPM) run mock:db:reset

typespec-compile:
	$(NPM) run typespec:compile

compile: typespec-compile

docs:
	PORT=$(PORT) $(NPM) run docs

build:
	$(NPM) run build

test:
	$(NPM) test

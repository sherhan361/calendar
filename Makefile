NPM ?= npm
PYTHON ?= python3
PORT ?= 8080
FRONTEND_DIR := frontend
BACKEND_DIR := backend
SPEC_DIR := spec
BACKEND_PYTHON ?= .venv/bin/python

.DEFAULT_GOAL := help

.PHONY: help install dev dev-web dev-api db-migrate db-revision db-seed db-reset typespec-compile compile docs build test

help:
	@printf "Available targets:\n"
	@printf "  make install              Install frontend and backend dependencies\n"
	@printf "  make dev                  Run FastAPI backend and Vite frontend\n"
	@printf "  make dev-web              Run Vite frontend only\n"
	@printf "  make dev-api              Run FastAPI backend only\n"
	@printf "  make db-migrate           Apply backend migrations\n"
	@printf "  make db-revision MSG=...  Create Alembic revision\n"
	@printf "  make db-seed              Seed local SQLite DB\n"
	@printf "  make db-reset             Recreate and seed local SQLite DB\n"
	@printf "  make typespec-compile     Compile TypeSpec/OpenAPI\n"
	@printf "  make compile              Alias for typespec-compile\n"
	@printf "  make docs [PORT=8080]     Serve local API docs\n"
	@printf "  make build                Build frontend\n"
	@printf "  make test                 Run contract, backend, and frontend checks\n"

install:
	$(NPM) --prefix $(FRONTEND_DIR) install
	$(NPM) --prefix $(SPEC_DIR) install
	$(PYTHON) -m venv $(BACKEND_DIR)/.venv
	cd $(BACKEND_DIR) && $(BACKEND_PYTHON) -m pip install -e ".[dev]"

dev:
	cd $(BACKEND_DIR) && $(BACKEND_PYTHON) scripts/dev.py

dev-web:
	$(NPM) --prefix $(FRONTEND_DIR) run dev

dev-api:
	cd $(BACKEND_DIR) && $(BACKEND_PYTHON) -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

db-migrate:
	cd $(BACKEND_DIR) && $(BACKEND_PYTHON) -m alembic upgrade head

db-revision:
	cd $(BACKEND_DIR) && $(BACKEND_PYTHON) -m alembic revision --autogenerate -m "$(MSG)"

db-seed:
	cd $(BACKEND_DIR) && $(BACKEND_PYTHON) scripts/seed.py

db-reset:
	rm -f $(BACKEND_DIR)/data/calendar.sqlite $(BACKEND_DIR)/data/calendar.sqlite-journal
	$(MAKE) db-migrate
	$(MAKE) db-seed

typespec-compile:
	$(NPM) --prefix $(SPEC_DIR) run compile

compile: typespec-compile

docs:
	PORT=$(PORT) $(NPM) --prefix $(FRONTEND_DIR) run docs

build:
	$(NPM) --prefix $(FRONTEND_DIR) run build

test:
	$(MAKE) typespec-compile
	cd $(BACKEND_DIR) && $(BACKEND_PYTHON) -m pytest
	$(MAKE) build

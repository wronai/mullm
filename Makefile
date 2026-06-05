SHELL := /bin/bash

COMPOSE ?= docker compose
PROFILES ?= core rag
NLP2DSL ?= 1
NLP2DSL_DIR ?= ../nlp2dsl
NLP2CMD ?= 1
NLP2CMD_DIR ?= ../nlp2cmd
NLP2DSL_BACKEND_HOST_PORT ?= 8010
NLP2DSL_NLP_HOST_PORT ?= 8012
NLP2DSL_WORKER_HOST_PORT ?= 8004

PROFILE_ARGS := $(foreach profile,$(PROFILES),--profile $(profile))

.DEFAULT_GOAL := help

.PHONY: help up down restart build logs ps test test-web test-e2e-live test-quality propact-pact smoke ensure-env ensure-nlp2dsl-env nlp2dsl-up nlp2dsl-down nlp2cmd-up nlp2cmd-down mullm-cli

help:
	@printf "Mullm targets:\n"
	@printf "  make up        Start Mullm (%s) and nlp2dsl when available\n" "$(PROFILES)"
	@printf "  make down      Stop Mullm and nlp2dsl when enabled\n"
	@printf "  make restart   Restart both stacks\n"
	@printf "  make build     Build Mullm services\n"
	@printf "  make logs      Tail Mullm logs\n"
	@printf "  make ps        Show Mullm containers\n"
	@printf "  make test      Run pytest\n"
	@printf "  make test-quality  pytest + intract + E2E (if web up)\n"
	@printf "  make smoke     Check public health endpoints\n"
	@printf "  make mullm-cli Print how to add scripts/mullm to PATH\n"
	@printf "\nOptions:\n"
	@printf "  PROFILES=\"core rag\"  Compose profiles for Mullm\n"
	@printf "  NLP2DSL=0             Do not manage ../nlp2dsl\n"
	@printf "  NLP2CMD=1             Start nlp2cmd profile in Mullm compose\n"
	@printf "  NLP2DSL_*_HOST_PORT   Override nlp2dsl smoke ports\n"

NLP2CMD_PROFILE_ARGS := $(if $(filter 1,$(NLP2CMD)),--profile nlp2cmd,)

up: ensure-env
	$(COMPOSE) $(PROFILE_ARGS) $(NLP2CMD_PROFILE_ARGS) up -d
	@if [ "$(NLP2DSL)" = "1" ]; then \
		$(MAKE) --no-print-directory nlp2dsl-up; \
	fi

down:
	@if [ "$(NLP2DSL)" = "1" ]; then \
		$(MAKE) --no-print-directory nlp2dsl-down; \
	fi
	$(COMPOSE) $(PROFILE_ARGS) $(NLP2CMD_PROFILE_ARGS) down

restart: down up

build: ensure-env
	$(COMPOSE) $(PROFILE_ARGS) build

logs:
	$(COMPOSE) $(PROFILE_ARGS) logs -f --tail=200

ps:
	$(COMPOSE) $(PROFILE_ARGS) ps

test:
	pytest -q

test-web:
	pip install -q -r requirements-dev.txt -r services/web/requirements.txt
	@[ -f requirements-quality.txt ] && pip install -q -r requirements-quality.txt || true
	pytest -c services/web/pytest.ini services/web/tests -q

test-e2e-live:
	pip install -q -r requirements-dev.txt -r services/web/requirements.txt
	chmod +x scripts/wait-for-web.sh
	./scripts/wait-for-web.sh
	MULLM_E2E=1 pytest -c services/web/pytest.ini services/web/tests/test_e2e_live_stack.py -v

test-quality:
	chmod +x scripts/test-quality.sh
	./scripts/test-quality.sh

test-quality-deps:
	pip install -q -r requirements-dev.txt -r services/web/requirements.txt -r requirements-quality.txt

propact-pact:
	chmod +x scripts/run-propact-pact.sh
	./scripts/run-propact-pact.sh

mullm-cli:
	@printf "Dodaj do PATH:\n  export PATH=\"$(CURDIR)/scripts:$$PATH\"\n"
	@printf "Potem: mullm chat send \"lista plikow usera\"\n"

smoke:
	curl -fsS http://127.0.0.1:3003/health
	curl -fsS http://127.0.0.1:3003/api/agents/status
	curl -fsS http://127.0.0.1:8001/health
	curl -fsS http://127.0.0.1:8002/health
	@if [ "$(NLP2DSL)" = "1" ] && [ -f "$(NLP2DSL_DIR)/docker-compose.yml" ]; then \
		curl -fsS -o /dev/null -w 'nlp2dsl backend: %{http_code}\n' http://127.0.0.1:$(NLP2DSL_BACKEND_HOST_PORT)/docs && \
		curl -fsS -o /dev/null -w 'nlp2dsl nlp: %{http_code}\n' http://127.0.0.1:$(NLP2DSL_NLP_HOST_PORT)/docs && \
		curl -fsS -o /dev/null -w 'nlp2dsl worker: %{http_code}\n' http://127.0.0.1:$(NLP2DSL_WORKER_HOST_PORT)/health; \
	fi
	@if [ "$(NLP2CMD)" = "1" ]; then \
		curl -fsS -o /dev/null -w 'nlp2cmd: %{http_code}\n' http://127.0.0.1:$${MULLM_NLP2CMD_HOST_PORT:-8020}/health; \
	fi

ensure-env:
	@if [ ! -f .env ] && [ -f .env.example ]; then \
		cp .env.example .env; \
		echo "Created .env from .env.example"; \
	fi

ensure-nlp2dsl-env:
	@if [ -f "$(NLP2DSL_DIR)/docker-compose.yml" ]; then \
		if [ ! -f "$(NLP2DSL_DIR)/.env" ] && [ -f "$(NLP2DSL_DIR)/.env.example" ]; then \
			cp "$(NLP2DSL_DIR)/.env.example" "$(NLP2DSL_DIR)/.env"; \
			echo "Created $(NLP2DSL_DIR)/.env from .env.example"; \
		fi; \
	fi

nlp2dsl-up: ensure-nlp2dsl-env
	@if [ -f "$(NLP2DSL_DIR)/docker-compose.yml" ]; then \
		cd "$(NLP2DSL_DIR)" && $(COMPOSE) up -d; \
	else \
		echo "Skipping nlp2dsl: $(NLP2DSL_DIR)/docker-compose.yml not found"; \
	fi

nlp2dsl-down:
	@if [ -f "$(NLP2DSL_DIR)/docker-compose.yml" ]; then \
		cd "$(NLP2DSL_DIR)" && $(COMPOSE) down; \
	else \
		echo "Skipping nlp2dsl: $(NLP2DSL_DIR)/docker-compose.yml not found"; \
	fi

nlp2cmd-up:
	$(COMPOSE) --profile nlp2cmd up -d nlp2cmd

nlp2cmd-down:
	$(COMPOSE) --profile nlp2cmd stop nlp2cmd

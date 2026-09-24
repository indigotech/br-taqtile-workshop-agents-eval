sources = app tests scripts

# pytest verbosity — override for a compact single-run summary, e.g. make test PYTEST_FLAGS=-q
PYTEST_FLAGS ?= -vv

# What pytest collects — override to narrow a run by path, e.g. make test TEST_PATH=tests/core
TEST_PATH ?= tests

.PHONY: help
help: ## Show this help message
	@echo "Usage: make [target]"
	@echo
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

.PHONY: install
install: ## Install Python (if needed) and the project dependencies
	@uv sync

.PHONY: list-outdated-dependencies
list-outdated-dependencies: ## List outdated direct dependencies
	@uv tree --outdated --depth 1

.PHONY: setup-env
setup-env: ## Create .env from sample.env (never overwrites an existing .env)
	@if [ -f .env ]; then echo ".env already exists, leaving it untouched."; else cp sample.env .env && echo "Created .env — fill in GEMINI_API_KEY."; fi

.PHONY: run
run: ## Start the terminal chat (reads .env)
	@uv run python -m app.cli

.PHONY: smoke-test
smoke-test: ## Run a real two-turn conversation (needs GEMINI_API_KEY) on a throwaway DB
	@uv run python -m scripts.smoke_test

# Runs per dataset case and an optional comma-separated case filter for run-dataset
RUNS ?= 1
CASES ?=

.PHONY: run-dataset
run-dataset: ## Run the eval dataset against the real API (RUNS=3 CASES=id1,id2), saving to evals/runs/
	@uv run python -m scripts.run_dataset --runs $(RUNS) $(if $(CASES),--cases $(CASES),)

.PHONY: evaluate
evaluate: ## Run the registered evaluators over a run-dataset result (RESULTS=evals/runs/<timestamp>/results.jsonl, LANGFUSE=1 to send scores)
	@if [ -z "$(RESULTS)" ]; then echo "RESULTS is required, e.g. make evaluate RESULTS=evals/runs/<timestamp>/results.jsonl"; exit 1; fi
	@uv run python -m scripts.evaluate_runs --results $(RESULTS) $(if $(LANGFUSE),--langfuse,)

.PHONY: reset-db
reset-db: ## Recreate the local SQLite database from the schema and seed it
	@uv run python -m scripts.reset_database

.PHONY: run-langfuse
run-langfuse: ## Start the local Langfuse stack (http://localhost:3000)
	@docker compose up -d
	@echo "Langfuse starting at http://localhost:$${LANGFUSE_PORT:-3000} (login: workshop@example.com / workshop123)"

.PHONY: stop-langfuse
stop-langfuse: ## Stop the local Langfuse stack, keeping its data
	@docker compose stop

.PHONY: clean-langfuse
clean-langfuse: ## Remove the local Langfuse stack and all of its traces
	@docker compose down --volumes --remove-orphans

.PHONY: test
test: ## Run tests (TEST_PATH narrows by path, ARGS forwards flags, e.g. make test ARGS="-k tool_loop")
	@uv run pytest $(TEST_PATH) $(PYTEST_FLAGS) $(ARGS)

.PHONY: test-ci
test-ci: ## Run tests with a compact one-shot summary
	@$(MAKE) test PYTEST_FLAGS="-q"

.PHONY: lint-check
lint-check: ## Run ruff check + ruff format check + mypy --strict
	@echo "Starting ruff check:"
	@uv run ruff check $(sources)
	@echo "Starting ruff format check:"
	@uv run ruff format --check $(sources)
	@echo "Starting mypy check:"
	@uv run mypy $(sources)

.PHONY: lint-fix
lint-fix: ## Auto-fix what ruff can and format the code; type errors need fixing by hand
	@uv run ruff check --fix --show-fixes $(sources)
	@$(MAKE) format

.PHONY: format
format: ## Format code
	@uv run ruff format $(sources)

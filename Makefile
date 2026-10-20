sources = app tests scripts evals

# On Windows the recipes still run in a POSIX shell: GNU Make picks up the sh.exe
# from Git for Windows' Git\bin when it is on PATH (scripts/setup_workshop.ps1
# puts it there). Python's default encoding there is the ANSI code page, which
# cannot print everything the model writes, hence UTF-8 mode.
ifeq ($(OS),Windows_NT)
VENV_PYTHON = $(CURDIR)/.venv/Scripts/python.exe
export PYTHONUTF8 = 1
else
VENV_PYTHON = $(CURDIR)/.venv/bin/python
endif

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
	@if [ -f .env ]; then echo ".env already exists, leaving it untouched."; else cp sample.env .env && echo "Created .env: fill in MODEL_API_KEY and the Langfuse keys."; fi

.PHONY: run
run: ## Start the terminal chat (reads .env)
	@uv run python -m app.cli

# Tool that run-case-tool-error makes fail on every call
ERROR_TOOL ?= search_accommodations

.PHONY: run-case-tool-error
run-case-tool-error: ## Start the chat with one tool failing on every call (ERROR_TOOL=search_accommodations)
	@FORCE_TOOL_ERROR=$(ERROR_TOOL) uv run python -m app.cli

# Tool that run-case-slow-tool makes take 5 extra seconds on every call
SLOW_TOOL ?= search_accommodations

.PHONY: run-case-slow-tool
run-case-slow-tool: ## Start the chat with one tool taking 5 extra seconds per call (SLOW_TOOL=search_accommodations)
	@FORCE_SLOW_TOOL=$(SLOW_TOOL) uv run python -m app.cli

.PHONY: smoke-test
smoke-test: ## Run a real two-turn conversation (needs MODEL_API_KEY) on a throwaway DB
	@uv run python -m scripts.smoke_test

# Runs per dataset case and an optional comma-separated case filter for run-dataset
RUNS ?= 1
CASES ?=

.PHONY: run-dataset
run-dataset: ## Run the eval dataset against the real API (RUNS=3 CASES=id1,id2), saving to evals/runs/
	@uv run python -m scripts.run_dataset --runs $(RUNS) $(if $(CASES),--cases $(CASES),)

# promptfoo's optional dependencies include Playwright, whose install script
# downloads Chromium for minutes; the judge evals never open a browser. The
# optional dependencies themselves stay: its SQLite binding is one of them.

.PHONY: install-judge
install-judge: ## Install promptfoo (needs Node 22.22+)
	@PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm ci

# promptfoo config that eval-judge runs — override for the judge consistency check
CONFIG ?= evals/judge/promptfooconfig.yaml

# No telemetry or update checks leave the machine, and promptfoo's results
# database stays in this checkout instead of ~/.promptfoo. promptfoo reads
# LOG_LEVEL too, but silently prints nothing with the uppercase value from .env.
PROMPTFOO = LOG_LEVEL=info NODE_NO_WARNINGS=1 PROMPTFOO_DISABLE_TELEMETRY=1 PROMPTFOO_DISABLE_UPDATE=1 PROMPTFOO_CONFIG_DIR=$(CURDIR)/.promptfoo npx --no-install promptfoo

.PHONY: eval-judge
eval-judge: ## Run a promptfoo LLM-as-a-judge eval, costs tokens (CONFIG=evals/judge/x.yaml, ARGS="--repeat 3")
	@PROMPTFOO_PYTHON=$(VENV_PYTHON) PYTHONPATH=$(CURDIR) $(PROMPTFOO) eval --config $(CONFIG) --no-cache $(ARGS)

.PHONY: view-judge
view-judge: ## Open the promptfoo results UI for the judge evals
	@$(PROMPTFOO) view --yes

.PHONY: reset-db
reset-db: ## Recreate the local SQLite database from the schema and seed it
	@uv run python -m scripts.reset_database

.PHONY: test
test: ## Run tests (TEST_PATH narrows by path, ARGS forwards flags, e.g. make test ARGS="-k tool_loop")
	@uv run pytest $(TEST_PATH) $(PYTEST_FLAGS) $(ARGS)

.PHONY: test-ci
test-ci: ## Run tests with a compact one-shot summary
	@$(MAKE) test PYTEST_FLAGS="-q"

# Target-specific, so they don't inherit the defaults of test (tests/) and
# run-dataset (RUNS=1); values passed on the command line still win.
test-model: TEST_PATH = evals/unit_tests
test-model: RUNS = 3

.PHONY: test-model
test-model: ## Run evals/unit_tests against the real API, costs tokens (RUNS=3, TEST_PATH, ARGS="-s -k ...")
	@RUNS=$(RUNS) uv run pytest $(TEST_PATH) $(PYTEST_FLAGS) $(ARGS)

# results.jsonl that eval-end-to-end checks; empty picks the latest in evals/runs/
RESULTS ?=

.PHONY: eval-end-to-end
eval-end-to-end: ## Check a make run-dataset results.jsonl against the golden dataset (RESULTS=evals/runs/x/results.jsonl, default the latest)
	@RESULTS=$(RESULTS) uv run pytest evals/unit_tests/test_end_to_end.py $(PYTEST_FLAGS) $(ARGS)

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

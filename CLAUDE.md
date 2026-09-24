# CLAUDE.md

A multi-agent weekend-trip planner ("planejador de rolê") that serves as the starting point of an agent-evaluation workshop. It is a terminal chat in Python that calls Gemini through the `google-genai` SDK directly — **no agent framework** — with a hand-written tool-calling loop, a local SQLite database, and a local Langfuse for traces.

**The agents are meant to be bad.** Later phases plant defects on purpose (prompts, orchestration, parameters) so the workshop's evaluation techniques have something to find. Those defects live in agent *behavior*; the *code* still follows every convention below. Never "fix" an agent's prompt or parameters unless the task asks for it.

## Verifying a Change

Everything goes through the `Makefile`; `make help` lists every target.

```bash
make install                         # once per checkout — installs Python 3.13 (via uv) and dependencies
make test-ci                         # the full suite, quiet output
make lint-check                      # ruff check + format check + mypy --strict, all CI gates
make lint-fix                        # auto-fix what ruff can; type errors need fixing by hand
```

`test.env` is committed and `tests/conftest.py` loads it (overriding any `.env`) before the app is imported, so testing needs no local configuration and never sends traces anywhere. Each test gets its own seeded SQLite file under `tmp_path`, so running `pytest` directly is safe — it can never touch `data/planner.db`. Use `make test TEST_PATH=tests/core` to narrow by path and `make test ARGS="-k tool_loop"` to narrow by name.

Tests never call the real Gemini API: use `ScriptedGeminiClient` from `tests/helpers.py`, which replays canned responses and records every request.

## Running Locally

```bash
make setup-env                       # creates .env from sample.env; then fill in GEMINI_API_KEY
make run-langfuse                    # local Langfuse at http://localhost:3000 (keys are pre-provisioned)
make run                             # terminal chat; creates and seeds the DB on first run
make reset-db                        # recreate data/planner.db from schema.sql + seed.sql
make smoke-test                      # real two-turn conversation on a throwaway DB (needs GEMINI_API_KEY)
make run-dataset RUNS=3              # play evals/dataset.jsonl N times, saving to evals/runs/ (needs GEMINI_API_KEY)
```

Set `LANGFUSE_TRACING_ENABLED=false` in `.env` to run without Langfuse.

## Architecture

A lean, by-layer take on the Clean Architecture used in Taqtile's AI projects, under `app/`:

- **`core/`** — innermost: config, logging, Langfuse observability, the Gemini client, the tool abstraction and registry, the tool-calling loop, and the `Agent` class every agent is built from.
- **`data/`** — the SQLite schema and seed, the connection helpers, row models, one datasource per aggregate, and the clients for external public APIs.
- **`tools/`** — concrete tools the model can call, each with a Pydantic input and output model.
- **`agents/`** — concrete agents: their prompts, the tools they get, and their model parameters. An orchestrator agent talks to the user and delegates to the specialists through `AgentTool`.
- **`evals/`** — the evaluation harness: dataset, runner and the extension points for the workshop's evaluators.
- **`cli.py`** — the terminal entrypoint.

Each layer has its own `CLAUDE.md` with detailed conventions — read it before working in that layer.

**Keep the docs honest.** If you notice any difference between what these `CLAUDE.md` files describe and the actual architecture or codebase, stop and prompt the user about it rather than silently following either side — the docs may be stale, or the code may have drifted.

### Dependency Rules

- **`core/`** imports from nothing else in `app/`. Any layer may import from it.
- **`data/`** imports only from `core/`.
- **`tools/`** imports from `data/` and `core/`.
- **`agents/`** imports from `tools/`, `data/` and `core/`; never from another agent's module except through the orchestrator.
- **`cli.py`** and **`evals/`** are composition roots and may import from anywhere; nothing else imports from them.

## Code Conventions

### No Abbreviations

Follow Clean Code — never use abbreviated names. Use full descriptive names (`error` not `err`, `connection` not `conn`, `user_data_source` not `ds`).

### Comments

Write a comment only to justify a decision the code cannot explain on its own — a non-obvious constraint, a subtle reason for an approach, a trap avoided. Never restate what a name or signature already says, and never describe what a class's callers do with it. Prefer a clearer name or a better-named test over a comment. Deliberate agent defects are the exception to "explain it in a comment": they are documented in the instructor's answer key, **never** in the repository, since students read this code.

### Typing & Formatting

- Python 3.13. Code must pass `mypy --strict` and `ruff check`.
- Use modern type syntax: `str | None`, `dict[str, Any]`, `list[User]` — not `Optional`/`Dict`/`List`.
- ruff handles formatting; never hand-format.

### Logging

Get a logger per module with `logging.getLogger(__name__)`. Use `%`-style lazy formatting (`logger.info("Tool %s succeeded", name)`) — **never f-strings in log calls**, which format eagerly even when the level is disabled.

### Function Placement

Write a file so its **primary function reads first**. Helper functions go **after** the function they support, not above it — a reader meets the entry point before the details. The same applies within a class: its public method first, its private helpers after.

### Instantiating Models

Prefer `PydanticModel.model_validate(source)` over the keyword constructor. It keeps conversions declarative and survives field changes without rethreading keyword arguments. Fall back to the keyword constructor only when **composing** a model from several sources with no single object to validate from.

### Models

**`BaseModel` is the only model type — never `NamedTuple`, `TypedDict`, or a dataclass.** Values that are transient (a tool execution, a loop result, an agent result) declare `ConfigDict(frozen=True)`. `frozen=True` is shallow — it blocks rebinding a field, not `model.some_list.append(...)`.

### `dict[str, Any]` is not a model

Data whose shape the code knows travels as a Pydantic model, in every signature that carries it. A `dict[str, Any]` there forfeits everything `mypy --strict` could give you.

When data arrives shapeless — a SQLite row, an external API response, the arguments of a function call from the model — validate it into a model **at the boundary that receives it** (the datasource, the API client, the tool registry) and pass the model onward. Reserve `dict[str, Any]` for payloads that are genuinely open-ended: the raw function-call arguments before validation, a tool's serialized output going back to the model, Langfuse metadata.

## Pull Requests

- Branches `feat/…` / `fix/…`; commits `feat(scope): …` / `fix(scope): …`.
- Small PRs in sequence. The description has **O quê / Por quê / Verificação** sections and links the Linear issue.

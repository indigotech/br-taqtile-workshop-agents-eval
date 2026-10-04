# evals/ — Evaluation Harness

The base the workshop's evals plug into: it plays the dataset and records what the system did. The evaluators themselves are built during the workshop on top of the `RunRecord`s. Like `cli.py`, this layer is a composition root and may import from any other layer; nothing in `app/` imports from it.

## Dataset (`dataset.py`, `evals/dataset.jsonl`)

One `EvalCase` per line of `evals/dataset.jsonl`: the user, the messages to play in order, and the references each technique needs — `expected_trip` (code-based checks), `required_agents` (which orchestrator tools must run on the first message), `user_preferences` (LLM-as-a-Judge rubric input), `confirmation_message_index` and `max_lodging_total` (booking risk), `reference_answer` (similarity).

Dates are **placeholders** (`{next_saturday}`, `{next_saturday_br}`, `{saturday_in_5_weeks}`, …) resolved by `load_dataset(path, today)`, because the weather forecast only covers ~16 days ahead. Every `RunRecord` stores its resolved case, so evaluating old results never re-resolves dates.

Keep the cases tied to the seed: user ids and catalog cities come from `app/data/seed.sql`. The budget is never stored, so a case states it in its messages, like a user would; `max_lodging_total` is the lodging limit that case states.

## Runner (`runner.py`, `records.py`)

`run_case` plays one case against the orchestrator on a **freshly seeded throwaway database** (runs never see each other's reservations) and returns a `RunRecord`: per turn, the response, each delegation to a specialist (`AgentCall`), reservations created, trace id, latency, and any model API error or turn over the token budget (either ends that run instead of the whole dataset). Between turns it carries the history the same way as the CLI (`next_turn_history`: the latest turn in full, earlier ones as text only). Traces are tagged `dataset` + the case id in Langfuse.

`make run-dataset RUNS=3 CASES=id1,id2` runs it against the real API and writes `evals/runs/<timestamp>/results.jsonl` (git-ignored). Each run makes a dozen or more model calls — narrow with `CASES` while iterating.

## Real-model unit tests (`evals/unit_tests/`)

pytest tests that call the **real model** — the workshop's checks on an agent's output (a regex over a reply, validating a structured response against its model) — live in `evals/unit_tests/`, never in `tests/`. `tests/` loads `test.env` and never calls the model; `evals/unit_tests/conftest.py` uses `.env` as-is, and pyproject's `testpaths = ["tests"]` keeps `make test` / `make test-ci` (and CI) from ever collecting them. Never run both directories in the same pytest invocation: whichever conftest loads first decides the configuration the app is built with.

- **No real key, no run.** The conftest checks `MODEL_API_KEY` (shell or `.env`) before anything under `app/` is imported; when it is missing or still a placeholder (`changethis`, `test`), every file there is skipped without being imported and the reason is printed. The check is `missing_model_api_key_reason` in `evals/unit_tests/model_api_key.py`, unit-tested in `tests/evals/`.
- **Fixtures:** `connection` (a freshly seeded throwaway SQLite file per test, as in `tests/`), `model_client` (a real `ModelClient()`), and `runs` (the `RUNS` environment variable, default 1).
- **Tracing** follows `.env`: each test is one Langfuse trace tagged `unit-test` (`unit_test_trace` in `evals/unit_tests/tracing.py`), flushed when the session ends. With `LANGFUSE_TRACING_ENABLED=false` nothing is sent. There is no per-test token budget, since a test repeating a turn `runs` times would exceed the per-turn one.
- **Generate once per file.** When several tests check the same agent output, a module-scoped fixture produces it `runs` times and every test in the file reuses it, so the file costs `runs` model calls instead of `runs` per test (see `itineraries` in `test_itinerary_format.py`). Such a fixture runs before the per-test trace exists, so it builds its own `ModelClient()` and wraps its body in `unit_test_trace(__name__)` to keep its calls tagged.
- `make test-model` runs them (`RUNS=5`, `TEST_PATH=evals/unit_tests/test_x.py`, `ARGS="-s -k name"`).

Every test costs tokens and its result varies from run to run: repeat a stochastic check `runs` times and assert a pass rate against a threshold rather than a single outcome, and narrow with `TEST_PATH` / `-k` while iterating.

# tests/ — Test Cases

Tests mirror the `app/` layout (`tests/core`, `tests/data`, `tests/tools`, `tests/agents`).

- `conftest.py` loads `test.env` over any `.env` **before** importing the app, and the `connection` fixture hands each test a freshly seeded SQLite file under `tmp_path`.
- Never call the real Gemini API. `tests/helpers.py` has `ScriptedGeminiClient` (replays responses, records requests) and the `text_response` / `function_call_response` builders.
- Tests are classes named `Test{Operation}`. **Name the test after the scenario it exercises**, not the mechanism (`test_model_that_never_stops_calling_tools_is_cut_at_the_limit`).
- When checking more than one field of the same object, assert the **whole dict at once** (`model.model_dump() == {...}`) so one comparison documents the full shape and fails with a single diff. Keep a single targeted assert only when the test verifies one field.
- Read database state back with plain SQL on the `connection`, not through the datasource under test.

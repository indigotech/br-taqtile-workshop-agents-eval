# evals/ — Evaluation Harness

The base the workshop's evals plug into. Like `cli.py`, this layer is a composition root and may import from any other layer; nothing in `app/` imports from it.

## Dataset (`dataset.py`, `evals/dataset.jsonl`)

One `EvalCase` per line of `evals/dataset.jsonl`: the user, the messages to play in order, and the references each technique needs — `expected_trip` (code-based checks), `required_agents` (which orchestrator tools must run on the first message), `user_preferences` (LLM-as-a-Judge rubric input), `confirmation_message_index` and `max_lodging_total` (booking risk), `reference_answer` (similarity).

Dates are **placeholders** (`{next_saturday}`, `{next_saturday_br}`, `{saturday_in_5_weeks}`, …) resolved by `load_dataset(path, today)`, because the weather forecast only covers ~16 days ahead. Every `RunRecord` stores its resolved case, so evaluating old results never re-resolves dates.

Keep the cases tied to the seed: user ids, budgets and catalog cities come from `app/data/seed.sql`.

## Runner (`runner.py`, `records.py`)

`run_case` plays one case against the orchestrator on a **freshly seeded throwaway database** (runs never see each other's reservations) and returns a `RunRecord`: per turn, the response, each delegation to a specialist (`AgentCall`), reservations created, trace id, latency, and any Gemini API error (which ends that run instead of the whole dataset). Traces are tagged `dataset` + the case id in Langfuse.

`make run-dataset RUNS=3 CASES=id1,id2` runs it against the real API and writes `evals/runs/<timestamp>/results.jsonl` (git-ignored). Each run makes a dozen or more model calls — narrow with `CASES` while iterating.

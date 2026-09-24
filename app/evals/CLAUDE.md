# evals/ — Evaluation Harness

The base the workshop's evals plug into. Like `cli.py`, this layer is a composition root and may import from any other layer; nothing in `app/` imports from it.

## Dataset (`dataset.py`, `evals/dataset.jsonl`)

One `EvalCase` per line of `evals/dataset.jsonl`: the user, the messages to play in order, and the references each technique needs — `expected_trip` (code-based checks), `required_agents` (which orchestrator tools must run on the first message), `user_preferences` (LLM-as-a-Judge rubric input), `confirmation_message_index` and `max_lodging_total` (booking risk), `reference_answer` (similarity).

Dates are **placeholders** (`{next_saturday}`, `{next_saturday_br}`, `{saturday_in_5_weeks}`, …) resolved by `load_dataset(path, today)`, because the weather forecast only covers ~16 days ahead. Every `RunRecord` stores its resolved case, so evaluating old results never re-resolves dates.

Keep the cases tied to the seed: user ids, budgets and catalog cities come from `app/data/seed.sql`.

## Runner (`runner.py`, `records.py`)

`run_case` plays one case against the orchestrator on a **freshly seeded throwaway database** (runs never see each other's reservations) and returns a `RunRecord`: per turn, the response, each delegation to a specialist (`AgentCall`), reservations created, trace id, latency, and any Gemini API error (which ends that run instead of the whole dataset). Traces are tagged `dataset` + the case id in Langfuse.

`make run-dataset RUNS=3 CASES=id1,id2` runs it against the real API and writes `evals/runs/<timestamp>/results.jsonl` (git-ignored). Each run makes a dozen or more model calls — narrow with `CASES` while iterating.

## Evaluators (`evaluators/`) — the extension point

An evaluator subclasses `Evaluator` (`evaluators/base.py`), sets a unique `name`, and implements `evaluate(record) -> EvaluationResult(passed, score 0-1, reason)`. One module per evaluator (`*_evaluator.py`), registered by appending an instance to `EVALUATORS` in `evaluators/__init__.py`. `CompletedWithoutErrorsEvaluator` is the reference example.

- What an evaluator can read: `record.case` (the references), and per turn `response`, `agent_calls` (name, instructions, response — the interpreter's raw output is the `interpret_request` call's response), `reservations_created`, `latency_seconds` and `trace_id`.
- Evaluators that need a model build a `GeminiClient` in their constructor: `generate(...)` for LLM-as-a-Judge, `embed(texts)` for cosine similarity. Those calls are traced like any other.
- An evaluator that raises is reported as failed with the error in its reason — it never aborts the report.

`make evaluate RESULTS=evals/runs/<timestamp>/results.jsonl` runs every registered evaluator, prints per case the passed runs, mean score, **pass@k** (at least one of the k runs passed) and **pass^k** (all k runs passed), and writes `evaluations.jsonl` next to the results. `LANGFUSE=1` also attaches each score to the run's Langfuse session.

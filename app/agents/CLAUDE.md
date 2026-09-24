# agents/ — Agents

Concrete agents, one module per agent (`*_agent.py`), each exposing a `build_*_agent(...)` factory that returns an `app.core.agent.Agent`. Imports from `tools/`, `data/` and `core/`.

## The agents

| Agent (`name`) | Orchestrator tool | Tools / capabilities |
| --- | --- | --- |
| `orchestrator` | — (talks to the user) | every agent below, through `AgentTool` |
| `input_interpreter` | `interpret_request` | none; `TripRequest` in its module is the contract its output is checked against |
| `database` | `query_database` | `get_database_snapshot`, `get_user_profile`, `list_user_reservations`, `search_accommodations` |
| `public_data` | `query_public_data` | `geocode_place`, `get_weather_forecast`, `list_public_holidays` |
| `research` | `search_web` | none |
| `budget_analyst` | `analyze_budget` | `get_user_profile`, `calculate_budget` |
| `action` | `execute_action` | `search_accommodations`, `create_reservation`, `record_decision` |
| `output_generator` | `generate_itinerary` | none |

The orchestrator is the only agent that sees the conversation; the others get a fresh one per call, holding only the `instructions` the orchestrator wrote. It is also the only module allowed to import other agents.

## Conventions

- The system prompt is a module-level constant next to its factory, in Portuguese. Per-conversation values (the user id) are formatted in by the factory.
- Model parameters (`model`, `temperature`, `max_iterations`) are set explicitly per agent in the factory, so each can be tuned on its own.
- Agents behave badly **on purpose** in this repository (see the root `CLAUDE.md`). Don't correct a prompt or parameter unless the task asks for it, and never add a comment pointing out a deliberate defect.
- Test agents with `ScriptedGeminiClient`: assert on what the agent *sent* (system prompt, tools declared, parameters) and on how it handled the scripted replies — never on the quality of a real model's answer, which is what the workshop's evals are for.

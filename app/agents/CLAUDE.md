# agents/ — Agents

Concrete agents, one module per agent (`*_agent.py`), each exposing a `build_*_agent(...)` factory that returns an `app.core.agent.Agent`. Imports from `tools/`, `data/` and `core/`.

- The system prompt is a module-level constant next to its factory, in Portuguese. Per-conversation values (the user id) are formatted in by the factory.
- Model parameters (`model`, `temperature`, `max_iterations`) are set explicitly per agent in the factory, so each can be tuned on its own.
- Agents behave badly **on purpose** in this repository (see the root `CLAUDE.md`). Don't correct a prompt or parameter unless the task asks for it, and never add a comment pointing out a deliberate defect.
- Test agents with `ScriptedGeminiClient`: assert on what the agent *sent* (system prompt, tools declared, parameters) and on how it handled the scripted replies — never on the quality of a real model's answer, which is what the workshop's evals are for.

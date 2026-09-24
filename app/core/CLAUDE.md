# core/ — Foundation

The **innermost layer**: stable primitives every agent reuses. It must never import from `data/`, `tools/`, `agents/` or `cli.py`.

## Configuration (`config.py`)

`Settings(BaseSettings)` loads from the environment / `.env`. Import the singleton `settings` everywhere — **never read `os.environ` directly elsewhere**. A setting with no default is required and the app fails fast at import without it. Every new setting goes, in the same PR, into `config.py`, `sample.env` (documented) and `test.env`.

## Observability (`observability.py`)

Thin context managers over the Langfuse v4 SDK (OpenTelemetry based), nested by the call stack:

- `observe_turn` — one **trace per user turn**, grouped by `session_id` into a Langfuse session per conversation (a whole-chat trace would only appear when the chat ends).
- `observe_agent` — an `agent` observation per `Agent.run`.
- `observe_generation` — a `generation` per Gemini call, with model, parameters and token usage. Opened only by `GeminiClient`.
- `observe_tool` — a `tool` observation per tool execution, with input, output and error. Opened only by `ToolRegistry`.

Latency comes from the observation timings for free. With `LANGFUSE_TRACING_ENABLED=false` every context manager still works and records nothing.

## Gemini (`gemini.py`)

`GeminiClient.generate` is the single place the SDK is called. The model comes from `settings.GEMINI_MODEL` unless the client or the call overrides it. The raw SDK call sits in `_generate_content` so test doubles override only that and still exercise the tracing.

## Tools (`tools.py`) and the loop (`tool_loop.py`)

A `Tool[InputT, OutputT]` declares `name`, `description`, `input_model` and `output_model`; its function declaration is the input model's JSON schema, so **field descriptions are part of the prompt**. `ToolRegistry.execute` never raises — unknown tools, invalid arguments and exceptions all become an `error` the model reads back.

`run_tool_loop` disables the SDK's automatic function calling on purpose and runs the calls itself, so each one becomes its own span. It appends the model's content exactly as returned (keeping thought signatures), answers every function call of a turn in one `user` content, and stops at the first plain-text answer or at `max_iterations`. Tools already in the config (Gemini built-ins such as `google_search`) run server side; the loop collects their grounding (search queries and web sources) into the result.

## Agent (`agent.py`)

`Agent` = name + system prompt + tools + model parameters (model, temperature, iteration limit), run through `run_tool_loop` inside its own agent span. Concrete agents live in `app/agents/` and are built from this class — don't subclass it to change the loop.

- `builtin_tools` takes Gemini server-side tools. Gemini 2.5 rejects `google_search` combined with function declarations in one request, so an agent gets one kind or the other.
- `response_model` asks for JSON matching that model's schema. The result text comes back **unparsed**: whether it validates is for the caller — or a workshop eval — to check.

## Agents as tools (`agent_tool.py`)

`AgentTool(agent, name, description)` wraps an agent as a tool taking free-text `instructions`, so the orchestrator delegates with an ordinary function call and the sub-agent's span nests under that tool span. Every call is a fresh conversation: the sub-agent only knows what the orchestrator wrote into `instructions`.

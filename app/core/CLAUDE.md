# core/ — Foundation

The **innermost layer**: stable primitives every agent reuses. It must never import from `data/`, `tools/`, `agents/` or `cli.py`.

## Configuration (`config.py`)

`Settings(BaseSettings)` loads from the environment / `.env`. Import the singleton `settings` everywhere — **never read `os.environ` directly elsewhere**. A setting with no default is required and the app fails fast at import without it. Every new setting goes, in the same PR, into `config.py`, `sample.env` (documented) and `test.env`.

## Terminal output (`terminal.py`) and logging (`logging.py`)

Every line the chat and the scripts print goes through `paint(text, Style.X)`, so each source is told apart at a glance: user prompt bold cyan, bot reply green, auxiliary info (trace URLs, agents called) blue, API error notices bold red, startup and system messages bold magenta. `setup_logging` colors each log line by level (DEBUG/INFO dim, WARNING yellow, ERROR red) through `LevelColorFormatter`.

Color is on only when the target stream is a TTY, decided per stream (stdout for `paint`, the handler's own stderr for logs), and off whenever `settings.NO_COLOR` is non-empty (https://no-color.org) — set in the shell or in `.env`.

## Observability (`observability.py`)

Thin context managers over the Langfuse v4 SDK (OpenTelemetry based), nested by the call stack:

- `observe_turn` — one **trace per user turn**, grouped by `session_id` into a Langfuse session per conversation (a whole-chat trace would only appear when the chat ends). Optional `tags` mark traces for filtering (the dataset runner tags its runs).
- `observe_agent` — an `agent` observation per `Agent.run`.
- `observe_generation` — a `generation` per model call, with model, parameters and token usage. Opened only by `ModelClient`.
- `observe_tool` — a `tool` observation per tool execution, with input, output and error. Opened only by `ToolRegistry`.
- `observe_embedding` — an `embedding` observation per `ModelClient.embed` call.

Latency comes from the observation timings for free. With `LANGFUSE_TRACING_ENABLED=false` every context manager still works and records nothing.

## Messages (`messages.py`)

The conversation travels as `ChatMessage` models in the Chat Completions shape (`user`, `assistant` with `tool_calls`, `tool` with `tool_call_id`) — never as the SDK's request `TypedDict`s. `as_param()` converts at the client boundary. The system prompt is not part of the history: each agent sends its own through `GenerationConfig`, which also carries temperature, the tools' `FunctionDeclaration`s and the optional response JSON schema.

## Model client (`model_client.py`)

`ModelClient.generate` is the single place the OpenAI SDK is called, through Chat Completions. It returns the reply as an assistant `ChatMessage`. The model comes from `settings.MODEL` unless the client or the call overrides it. The raw SDK calls sit in `_create_completion` and `_create_embeddings` so test doubles override only those and still exercise the response conversion and the tracing.

- `settings.MODEL_BASE_URL` points the client at any provider with a Chat Completions compatible endpoint (DeepSeek, Gemini's OpenAI endpoint); unset means OpenAI.
- `settings.MODEL_REASONING_EFFORT` (default `none`) goes on every request: gpt-6-luna rejects function tools and any non-default temperature on Chat Completions while reasoning is on. Empty leaves the parameter out for providers that don't know it.
- The SDK client retries rate limits (429) and transient 5xx with exponential backoff (`_MAX_RETRIES`): one orchestrated turn makes a dozen or more calls.
- `embed(texts)` returns one vector per text with `settings.MODEL_EMBEDDING_MODEL` — the building block for cosine-similarity evals.

## Tools (`tools.py`) and the loop (`tool_loop.py`)

A `Tool[InputT, OutputT]` declares `name`, `description`, `input_model` and `output_model`; its function declaration is the input model's JSON schema, so **field descriptions are part of the prompt**. `ToolRegistry.execute` takes the arguments as a dict or as the raw JSON string of a tool call, and never raises — malformed JSON, unknown tools, invalid arguments and exceptions all become an `error` the model reads back.

`settings.FORCE_TOOL_ERROR` names a tool that fails on every call with a timeout, through the same path as a real exception, so a live demo can show an `ERROR` span. Only `make run-case-tool-error` sets it, from the shell environment. `settings.FORCE_SLOW_TOOL` works the same way for latency: that tool takes 5 extra seconds per call, so the slowest span is predictable in a demo; only `make run-case-slow-tool` sets it.

`run_tool_loop` runs the tool calls itself, so each one becomes its own span. It appends the model's reply exactly as returned (tool call ids and raw arguments included, since the next request must replay them), answers each tool call with its own `tool` message, and stops at the first plain-text answer or at `max_iterations`.

## Agent (`agent.py`)

`Agent` = name + system prompt + tools + model parameters (model, temperature, iteration limit), run through `run_tool_loop` inside its own agent span. Concrete agents live in `app/agents/` and are built from this class — don't subclass it to change the loop.

- `response_model` asks for JSON matching that model's schema. The result text comes back **unparsed**: whether it validates is for the caller — or a workshop eval — to check.

## Agents as tools (`agent_tool.py`)

`AgentTool(agent, name, description)` wraps an agent as a tool taking free-text `instructions`, so the orchestrator delegates with an ordinary function call and the sub-agent's span nests under that tool span. Every call is a fresh conversation: the sub-agent only knows what the orchestrator wrote into `instructions`.

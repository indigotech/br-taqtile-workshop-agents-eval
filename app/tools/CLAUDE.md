# tools/ — Tools

Concrete functions the model can call, one module per tool (`*_tool.py`). Imports from `data/` and `core/`.

- Subclass `app.core.tools.Tool[InputModel, OutputModel]` and set `name`, `description`, `input_model`, `output_model`.
- **The input model is the prompt.** Its JSON schema becomes the function declaration, so every field carries a `Field(description=...)` written for the model, in Portuguese like the prompts. Tool `name`s are `snake_case` verbs (`get_user_profile`).
- Dependencies (datasources, API clients) come in through the constructor; a tool never opens a connection.
- A tool returns its output model and lets unexpected errors propagate — `ToolRegistry` turns them into an error the model sees. Expected "nothing found" cases are part of the output model (`found: bool`), not exceptions.
- Test tools through `ToolRegistry.execute`, the same path the loop uses, against the `connection` fixture.

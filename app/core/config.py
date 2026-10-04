from pathlib import Path
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )

    ENVIRONMENT: Literal["test", "local"] = "local"
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    MODEL_API_KEY: str
    MODEL: str = "gpt-6-luna"
    MODEL_EMBEDDING_MODEL: str = "text-embedding-3-small"
    # None means OpenAI itself; any other provider with a Chat Completions
    # compatible endpoint works by pointing this at it.
    MODEL_BASE_URL: str | None = None
    # Reasoning models such as gpt-6-luna only accept function tools and a
    # non-default temperature through Chat Completions with reasoning off.
    # Empty leaves the parameter out, for providers that do not know it.
    MODEL_REASONING_EFFORT: str | None = "none"

    # https://no-color.org: any non-empty value turns terminal colors off. Read
    # from the shell environment as well as .env, like every setting.
    NO_COLOR: str | None = None

    DATABASE_PATH: Path = Path("data/planner.db")

    # Guards against an agent that keeps asking for tools forever; the loop gives
    # up and returns whatever the model said last.
    TOOL_LOOP_MAX_ITERATIONS: int = 10

    LANGFUSE_TRACING_ENABLED: bool = True
    LANGFUSE_BASE_URL: str = "http://localhost:3000"
    LANGFUSE_PUBLIC_KEY: str | None = None
    LANGFUSE_SECRET_KEY: str | None = None

    @model_validator(mode="after")
    def _require_langfuse_keys_when_tracing(self) -> "Settings":
        if self.LANGFUSE_TRACING_ENABLED and not (
            self.LANGFUSE_PUBLIC_KEY and self.LANGFUSE_SECRET_KEY
        ):
            raise ValueError(
                "LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY must be set when "
                "LANGFUSE_TRACING_ENABLED is true"
            )
        return self


settings = Settings()

from app.core.config import Settings


def test_log_level_is_case_insensitive() -> None:
    settings = Settings.model_validate(
        {
            "MODEL_API_KEY": "test",
            "LOG_LEVEL": "info",
            "LANGFUSE_TRACING_ENABLED": False,
        }
    )

    assert settings.LOG_LEVEL == "INFO"

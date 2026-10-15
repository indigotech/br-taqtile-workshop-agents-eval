import logging

import pytest

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


def test_tracing_turns_off_with_a_warning_when_a_langfuse_key_is_empty(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.WARNING, logger="app.core.config"):
        settings = Settings.model_validate(
            {
                "MODEL_API_KEY": "test",
                "LANGFUSE_TRACING_ENABLED": True,
                "LANGFUSE_PUBLIC_KEY": "pk-lf-student",
                "LANGFUSE_SECRET_KEY": "",
            }
        )

    assert settings.LANGFUSE_TRACING_ENABLED is False
    assert "tracing is off" in caplog.text


def test_tracing_stays_on_when_both_langfuse_keys_are_set() -> None:
    settings = Settings.model_validate(
        {
            "MODEL_API_KEY": "test",
            "LANGFUSE_TRACING_ENABLED": True,
            "LANGFUSE_PUBLIC_KEY": "pk-lf-student",
            "LANGFUSE_SECRET_KEY": "sk-lf-student",
        }
    )

    assert settings.LANGFUSE_TRACING_ENABLED is True

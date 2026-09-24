import logging

from app.core.config import settings

_FORMAT = "[%(levelname)s - %(name)s:%(lineno)d]: %(message)s"

# Third-party loggers that flood DEBUG output with HTTP and OTel internals,
# drowning the agent and tool logs the workshop is about.
_NOISY_LOGGERS = ("httpx", "httpcore", "google_genai", "langfuse", "opentelemetry")


def setup_logging() -> None:
    logging.basicConfig(level=settings.LOG_LEVEL, format=_FORMAT, force=True)
    for logger_name in _NOISY_LOGGERS:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

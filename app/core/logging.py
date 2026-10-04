import logging

from app.core.config import settings
from app.core.terminal import colorize, style_for_log_level, supports_color

_FORMAT = "[%(levelname)s - %(name)s:%(lineno)d]: %(message)s"

# Third-party loggers that flood DEBUG output with HTTP and OTel internals,
# drowning the agent and tool logs the workshop is about.
_NOISY_LOGGERS = ("httpx", "httpcore", "openai", "langfuse", "opentelemetry")


def setup_logging() -> None:
    handler = logging.StreamHandler()
    # Decided from the handler's own stream (stderr): piping stdout elsewhere
    # must not strip colors from logs still shown in the terminal, nor the reverse.
    handler.setFormatter(
        LevelColorFormatter(_FORMAT, use_color=supports_color(handler.stream))
    )
    logging.basicConfig(level=settings.LOG_LEVEL, handlers=[handler], force=True)
    for logger_name in _NOISY_LOGGERS:
        logging.getLogger(logger_name).setLevel(logging.WARNING)


class LevelColorFormatter(logging.Formatter):
    def __init__(self, format_string: str, *, use_color: bool) -> None:
        super().__init__(format_string)
        self._use_color = use_color

    def format(self, record: logging.LogRecord) -> str:
        line = super().format(record)
        if not self._use_color:
            return line
        return colorize(line, style_for_log_level(record.levelno))

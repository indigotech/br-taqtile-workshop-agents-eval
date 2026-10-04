import logging
import sys
from enum import StrEnum
from typing import TextIO

from app.core.config import settings

_RESET = "\033[0m"


class Style(StrEnum):
    USER_PROMPT = "\033[1;36m"
    BOT_REPLY = "\033[32m"
    AUXILIARY = "\033[34m"
    API_ERROR = "\033[1;31m"
    SYSTEM = "\033[1;35m"
    LOG_DEBUG = "\033[2m"
    LOG_INFO = "\033[2m"
    LOG_WARNING = "\033[33m"
    LOG_ERROR = "\033[31m"


def paint(text: str, style: Style, stream: TextIO | None = None) -> str:
    if not supports_color(sys.stdout if stream is None else stream):
        return text
    return colorize(text, style)


def colorize(text: str, style: Style) -> str:
    return f"{style}{text}{_RESET}"


def supports_color(stream: TextIO) -> bool:
    if settings.NO_COLOR:
        return False
    return stream.isatty()


def style_for_log_level(level: int) -> Style:
    if level >= logging.ERROR:
        return Style.LOG_ERROR
    if level >= logging.WARNING:
        return Style.LOG_WARNING
    if level >= logging.INFO:
        return Style.LOG_INFO
    return Style.LOG_DEBUG

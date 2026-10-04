import logging

from app.core.logging import LevelColorFormatter


def _record(level: int) -> logging.LogRecord:
    return logging.LogRecord(
        name="app.core.tools",
        level=level,
        pathname="tools.py",
        lineno=103,
        msg="Tool %s succeeded",
        args=("echo",),
        exc_info=None,
    )


class TestFormat:
    def test_colored_warning_is_wrapped_in_yellow(self) -> None:
        formatter = LevelColorFormatter("%(levelname)s %(message)s", use_color=True)

        line = formatter.format(_record(logging.WARNING))

        assert line == "\033[33mWARNING Tool echo succeeded\033[0m"

    def test_colored_info_is_dimmed(self) -> None:
        formatter = LevelColorFormatter("%(levelname)s %(message)s", use_color=True)

        line = formatter.format(_record(logging.INFO))

        assert line == "\033[2mINFO Tool echo succeeded\033[0m"

    def test_without_color_the_line_is_the_plain_format(self) -> None:
        formatter = LevelColorFormatter(
            "[%(levelname)s - %(name)s:%(lineno)d]: %(message)s", use_color=False
        )

        line = formatter.format(_record(logging.ERROR))

        assert line == "[ERROR - app.core.tools:103]: Tool echo succeeded"

import io
import logging

import pytest

from app.core.config import settings
from app.core.terminal import Style, paint, style_for_log_level


class TerminalStream(io.StringIO):
    def isatty(self) -> bool:
        return True


class TestPaint:
    def test_text_for_a_terminal_is_wrapped_in_the_style_and_a_reset(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "NO_COLOR", None)

        painted = paint("planejador> oi", Style.BOT_REPLY, TerminalStream())

        assert painted == "\033[32mplanejador> oi\033[0m"

    def test_text_piped_to_a_file_stays_plain(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "NO_COLOR", None)

        painted = paint("planejador> oi", Style.BOT_REPLY, io.StringIO())

        assert painted == "planejador> oi"

    def test_no_color_set_keeps_terminal_text_plain(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "NO_COLOR", "1")

        painted = paint("planejador> oi", Style.BOT_REPLY, TerminalStream())

        assert painted == "planejador> oi"

    def test_empty_no_color_does_not_disable_colors(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "NO_COLOR", "")

        painted = paint("você> ", Style.USER_PROMPT, TerminalStream())

        assert painted == "\033[1;36mvocê> \033[0m"

    def test_without_a_stream_the_decision_follows_stdout(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "NO_COLOR", None)
        monkeypatch.setattr("sys.stdout", TerminalStream())

        painted = paint("  trace: url", Style.AUXILIARY)

        assert painted == "\033[34m  trace: url\033[0m"


class TestStyleForLogLevel:
    def test_each_level_gets_its_own_style(self) -> None:
        styles = {
            level: style_for_log_level(level)
            for level in (
                logging.DEBUG,
                logging.INFO,
                logging.WARNING,
                logging.ERROR,
                logging.CRITICAL,
            )
        }

        assert styles == {
            logging.DEBUG: Style.LOG_DEBUG,
            logging.INFO: Style.LOG_INFO,
            logging.WARNING: Style.LOG_WARNING,
            logging.ERROR: Style.LOG_ERROR,
            logging.CRITICAL: Style.LOG_ERROR,
        }

    def test_log_styles_never_match_the_bot_reply(self) -> None:
        log_styles = {style_for_log_level(level) for level in range(0, 60, 10)}

        assert Style.BOT_REPLY not in log_styles

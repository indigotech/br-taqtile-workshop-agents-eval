import sqlite3
from collections.abc import Callable, Iterator

import httpx
import pytest

from app.cli import onboard_user
from app.data.city_data_source import CityDataSource
from app.data.models import User
from app.data.nominatim_client import NominatimClient
from app.data.user_data_source import UserDataSource
from tests.helpers import mock_http_client

_CURITIBA = {
    "name": "Curitiba",
    "display_name": "Curitiba, Paraná, Brasil",
    "lat": "-25.4295963",
    "lon": "-49.2712724",
}


def _onboard(
    connection: sqlite3.Connection,
    monkeypatch: pytest.MonkeyPatch,
    answers: list[str],
    geocoder: Callable[[httpx.Request], httpx.Response] | None = None,
) -> User | None:
    """Plays the answers as stdin; running out of them is a closed stdin."""
    remaining: Iterator[str] = iter(answers)

    def scripted_input(prompt: str = "") -> str:
        try:
            return next(remaining)
        except StopIteration:
            raise EOFError from None

    monkeypatch.setattr("builtins.input", scripted_input)
    return onboard_user(
        UserDataSource(connection),
        CityDataSource(connection),
        NominatimClient(mock_http_client(geocoder or _unexpected_geocoding)),
    )


def _unexpected_geocoding(request: httpx.Request) -> httpx.Response:
    raise AssertionError(f"Unexpected geocoding request: {request.url}")


def _count(connection: sqlite3.Connection, table: str) -> int:
    count: int = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    return count


class TestOnboardUser:
    def test_registered_user_found_by_first_name_goes_straight_to_the_trip(
        self,
        connection: sqlite3.Connection,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        user = _onboard(connection, monkeypatch, ["bruno", "s"])

        assert user is not None
        assert user.id == 2
        assert "Encontrei o cadastro de Bruno Lima, de São Paulo." in (
            capsys.readouterr().out
        )

    def test_several_matches_let_the_person_pick_by_number(
        self, connection: sqlite3.Connection, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        connection.execute(
            "INSERT INTO users (name, email, home_city_id)"
            " VALUES ('Ana Lima', 'ana.lima@example.com', 2)"
        )

        user = _onboard(connection, monkeypatch, ["Ana", "7", "2"])

        assert user is not None
        assert user.name == "Ana Lima"

    def test_unknown_name_that_declines_registration_is_thanked_and_leaves(
        self,
        connection: sqlite3.Connection,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        user = _onboard(connection, monkeypatch, ["Fernanda", "talvez", "não"])

        output = capsys.readouterr().out
        assert user is None
        assert "Não encontrei nenhum cadastro com o nome Fernanda." in output
        assert "Responda com s ou n, por favor." in output
        assert "Obrigado pela visita" in output
        assert _count(connection, "users") == 4

    def test_registration_in_a_known_city_reuses_it_without_geocoding(
        self, connection: sqlite3.Connection, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        user = _onboard(
            connection,
            monkeypatch,
            ["Fernanda", "s", "Fernanda Dias", "sao paulo", "Fernanda@Example.com"],
        )

        assert user is not None
        row = connection.execute(
            "SELECT name, email, home_city_id FROM users WHERE id = ?", (user.id,)
        ).fetchone()
        assert dict(row) == {
            "name": "Fernanda Dias",
            "email": "fernanda@example.com",
            "home_city_id": 1,
        }

    def test_person_who_is_not_the_match_registers_with_the_typed_name(
        self, connection: sqlite3.Connection, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        user = _onboard(
            connection,
            monkeypatch,
            ["Carla", "n", "s", "", "Rio de Janeiro", "carla2@example.com"],
        )

        assert user is not None
        assert (user.name, user.home_city_id) == ("Carla", 2)

    def test_registration_in_a_new_city_geocodes_and_stores_it(
        self, connection: sqlite3.Connection, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        queries: list[str | None] = []

        def geocoder(request: httpx.Request) -> httpx.Response:
            queries.append(request.url.params.get("q"))
            return httpx.Response(200, json=[_CURITIBA] if len(queries) > 1 else [])

        user = _onboard(
            connection,
            monkeypatch,
            [
                "Gabi",
                "s",
                "Gabriela Nunes",
                "Curitba",
                "PR",
                "",
                "curitiba",
                "PR",
                "",
                "gabi@example.com",
            ],
            geocoder,
        )

        assert user is not None
        assert queries == ["Curitba, PR, Brasil", "curitiba, PR, Brasil"]
        city = connection.execute(
            "SELECT name, state, country, latitude, longitude FROM cities WHERE id = ?",
            (user.home_city_id,),
        ).fetchone()
        assert dict(city) == {
            "name": "Curitiba",
            "state": "PR",
            "country": "Brasil",
            "latitude": -25.4295963,
            "longitude": -49.2712724,
        }

    def test_map_offline_asks_for_the_city_again_instead_of_failing(
        self,
        connection: sqlite3.Connection,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        user = _onboard(
            connection,
            monkeypatch,
            ["Joana", "s", "", "Gramado", "RS", "", "Ouro Preto", "joana@example.com"],
            lambda request: httpx.Response(503),
        )

        assert user is not None
        assert user.home_city_id == 7
        assert "Não consegui consultar o mapa agora." in capsys.readouterr().out

    def test_email_already_in_use_is_asked_again(
        self,
        connection: sqlite3.Connection,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        user = _onboard(
            connection,
            monkeypatch,
            [
                "Helena",
                "s",
                "",
                "Paraty",
                "sem-arroba",
                "ANA@example.com",
                "helena@example.com",
            ],
        )

        output = capsys.readouterr().out
        assert user is not None
        assert user.email == "helena@example.com"
        assert "Esse e-mail não parece válido." in output
        assert "Esse e-mail já está em outro cadastro." in output

    def test_exit_command_during_registration_creates_nothing(
        self, connection: sqlite3.Connection, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        user = _onboard(connection, monkeypatch, ["Igor", "s", "Igor Reis", "sair"])

        assert user is None
        assert _count(connection, "users") == 4

    def test_closed_input_ends_the_onboarding(
        self, connection: sqlite3.Connection, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        assert _onboard(connection, monkeypatch, []) is None

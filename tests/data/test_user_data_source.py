import sqlite3

from app.data.user_data_source import UserDataSource


class TestGetUser:
    def test_existing_user(self, connection: sqlite3.Connection) -> None:
        user = UserDataSource(connection).get_user(1)

        assert user is not None
        assert user.model_dump() == {
            "id": 1,
            "name": "Ana Souza",
            "email": "ana@example.com",
            "home_city_id": 1,
        }

    def test_missing_user(self, connection: sqlite3.Connection) -> None:
        assert UserDataSource(connection).get_user(999) is None


class TestListUsers:
    def test_all_seeded_users_in_id_order(self, connection: sqlite3.Connection) -> None:
        users = UserDataSource(connection).list_users()

        assert [user.id for user in users] == [1, 2, 3, 4]


class TestFindByName:
    def test_first_name_ignoring_case_and_spaces_finds_the_user(
        self, connection: sqlite3.Connection
    ) -> None:
        users = UserDataSource(connection).find_by_name("  ANA ")

        assert [user.name for user in users] == ["Ana Souza"]

    def test_full_name_typed_without_accents(
        self, connection: sqlite3.Connection
    ) -> None:
        connection.execute(
            "INSERT INTO users (name, email, home_city_id)"
            " VALUES ('Júlia Araújo', 'julia@example.com', 1)"
        )

        users = UserDataSource(connection).find_by_name("julia araujo")

        assert [user.name for user in users] == ["Júlia Araújo"]

    def test_shared_first_name_returns_every_match_in_id_order(
        self, connection: sqlite3.Connection
    ) -> None:
        connection.execute(
            "INSERT INTO users (name, email, home_city_id)"
            " VALUES ('Ana Lima', 'ana.lima@example.com', 2)"
        )

        users = UserDataSource(connection).find_by_name("Ana")

        assert [user.name for user in users] == ["Ana Souza", "Ana Lima"]

    def test_surname_alone_does_not_match(self, connection: sqlite3.Connection) -> None:
        assert UserDataSource(connection).find_by_name("Souza") == []

    def test_blank_name_matches_nobody(self, connection: sqlite3.Connection) -> None:
        assert UserDataSource(connection).find_by_name("   ") == []


class TestFindByEmail:
    def test_match_ignores_case(self, connection: sqlite3.Connection) -> None:
        user = UserDataSource(connection).find_by_email("Bruno@Example.com")

        assert user is not None
        assert user.id == 2

    def test_unknown_email(self, connection: sqlite3.Connection) -> None:
        assert UserDataSource(connection).find_by_email("nobody@example.com") is None


class TestCreateUser:
    def test_new_user_is_stored_and_returned_with_its_generated_id(
        self, connection: sqlite3.Connection
    ) -> None:
        user = UserDataSource(connection).create_user(
            "Elisa Prado", "elisa@example.com", 8
        )

        row = connection.execute(
            "SELECT id, name, email, home_city_id FROM users"
            " WHERE email = 'elisa@example.com'"
        ).fetchone()
        assert (
            user.model_dump()
            == dict(row)
            == {
                "id": 5,
                "name": "Elisa Prado",
                "email": "elisa@example.com",
                "home_city_id": 8,
            }
        )


class TestListPreferences:
    def test_preferences_in_insertion_order(
        self, connection: sqlite3.Connection
    ) -> None:
        preferences = UserDataSource(connection).list_preferences(3)

        assert [preference.model_dump() for preference in preferences] == [
            {"category": "food", "value": "comida italiana"},
            {"category": "activity", "value": "museus"},
            {"category": "lodging", "value": "hotel"},
            {"category": "restriction", "value": "vegetariana"},
        ]

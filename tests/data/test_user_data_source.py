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


class TestGetBudget:
    def test_existing_budget(self, connection: sqlite3.Connection) -> None:
        budget = UserDataSource(connection).get_budget(2)

        assert budget is not None
        assert budget.model_dump() == {
            "user_id": 2,
            "total_amount": 600.0,
            "lodging_amount": 250.0,
            "food_amount": 250.0,
            "activities_amount": 100.0,
            "currency": "BRL",
        }

    def test_missing_budget(self, connection: sqlite3.Connection) -> None:
        assert UserDataSource(connection).get_budget(999) is None


class TestListPreferences:
    def test_preferences_in_insertion_order(
        self, connection: sqlite3.Connection
    ) -> None:
        preferences = UserDataSource(connection).list_preferences(3)

        assert [preference.model_dump() for preference in preferences] == [
            {"category": "food", "value": "frutos do mar"},
            {"category": "activity", "value": "museus"},
            {"category": "lodging", "value": "hotel"},
            {"category": "restriction", "value": "vegetariana"},
        ]

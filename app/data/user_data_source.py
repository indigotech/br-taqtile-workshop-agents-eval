import sqlite3

from app.data.models import Budget, Preference, User


class UserDataSource:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def get_user(self, user_id: int) -> User | None:
        row = self.connection.execute(
            "SELECT id, name, email, home_city_id FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        return User.model_validate(dict(row)) if row else None

    def list_users(self) -> list[User]:
        rows = self.connection.execute(
            "SELECT id, name, email, home_city_id FROM users ORDER BY id"
        ).fetchall()
        return [User.model_validate(dict(row)) for row in rows]

    def get_budget(self, user_id: int) -> Budget | None:
        row = self.connection.execute(
            "SELECT user_id, total_amount, lodging_amount, food_amount,"
            " activities_amount, currency FROM budgets WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        return Budget.model_validate(dict(row)) if row else None

    def list_preferences(self, user_id: int) -> list[Preference]:
        rows = self.connection.execute(
            "SELECT category, value FROM preferences WHERE user_id = ? ORDER BY id",
            (user_id,),
        ).fetchall()
        return [Preference.model_validate(dict(row)) for row in rows]

import sqlite3

from app.data.models import Preference, User
from app.data.name_matching import normalize_name

_USER_COLUMNS = "id, name, email, home_city_id"


class UserDataSource:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def get_user(self, user_id: int) -> User | None:
        row = self.connection.execute(
            f"SELECT {_USER_COLUMNS} FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        return User.model_validate(dict(row)) if row else None

    def find_by_name(self, name: str) -> list[User]:
        """Users whose name starts with the given words, ignoring case and
        accents: "ana" finds "Ana Souza", "souza" does not."""
        wanted_words = normalize_name(name).split()
        if not wanted_words:
            return []
        return [
            user
            for user in self.list_users()
            if normalize_name(user.name).split()[: len(wanted_words)] == wanted_words
        ]

    def find_by_email(self, email: str) -> User | None:
        row = self.connection.execute(
            f"SELECT {_USER_COLUMNS} FROM users WHERE lower(email) = lower(?)",
            (email.strip(),),
        ).fetchone()
        return User.model_validate(dict(row)) if row else None

    def list_users(self) -> list[User]:
        rows = self.connection.execute(
            f"SELECT {_USER_COLUMNS} FROM users ORDER BY id"
        ).fetchall()
        return [User.model_validate(dict(row)) for row in rows]

    def create_user(self, name: str, email: str, home_city_id: int) -> User:
        cursor = self.connection.execute(
            "INSERT INTO users (name, email, home_city_id) VALUES (?, ?, ?)",
            (name, email, home_city_id),
        )
        self.connection.commit()
        row = self.connection.execute(
            f"SELECT {_USER_COLUMNS} FROM users WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
        return User.model_validate(dict(row))

    def list_preferences(self, user_id: int) -> list[Preference]:
        rows = self.connection.execute(
            "SELECT category, value FROM preferences WHERE user_id = ? ORDER BY id",
            (user_id,),
        ).fetchall()
        return [Preference.model_validate(dict(row)) for row in rows]

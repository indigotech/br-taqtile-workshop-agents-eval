import sqlite3

from app.data.models import Decision

_DECISION_COLUMNS = "id, user_id, reservation_id, summary, created_at"


class DecisionDataSource:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def create(
        self, user_id: int, reservation_id: int | None, summary: str
    ) -> Decision:
        cursor = self.connection.execute(
            "INSERT INTO decisions (user_id, reservation_id, summary) VALUES (?, ?, ?)",
            (user_id, reservation_id, summary),
        )
        self.connection.commit()
        row = self.connection.execute(
            f"SELECT {_DECISION_COLUMNS} FROM decisions WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
        return Decision.model_validate(dict(row))

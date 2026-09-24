from pathlib import Path

from app.data.database import connect, reset_database


class TestResetDatabase:
    def test_reset_discards_local_changes_and_reseeds(self, tmp_path: Path) -> None:
        database_path = tmp_path / "nested" / "planner.db"
        reset_database(database_path)
        connection = connect(database_path)
        connection.execute("DELETE FROM reservations")
        connection.commit()
        connection.close()

        reset_database(database_path)

        connection = connect(database_path)
        counts = {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in (
                "cities",
                "users",
                "budgets",
                "preferences",
                "accommodations",
                "reservations",
                "decisions",
            )
        }
        connection.close()
        assert counts == {
            "cities": 8,
            "users": 4,
            "budgets": 4,
            "preferences": 14,
            "accommodations": 15,
            "reservations": 4,
            "decisions": 0,
        }

    def test_foreign_keys_are_enforced(self, tmp_path: Path) -> None:
        database_path = tmp_path / "planner.db"
        reset_database(database_path)
        connection = connect(database_path)

        foreign_keys_enabled = connection.execute("PRAGMA foreign_keys").fetchone()[0]
        connection.close()

        assert foreign_keys_enabled == 1

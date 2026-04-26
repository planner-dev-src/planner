import sqlite3
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Column:
    id: str
    name: str
    position: int
    is_done_column: bool


@dataclass
class Task:
    id: str
    title: str
    column_id: str


class Board:
    def __init__(self, db_path: Optional[str] = None):
        base_dir = Path(__file__).resolve().parents[2]
        self.db_path = str(base_dir / "planner.db") if db_path is None else db_path
        self._init_db()
        self._ensure_default_columns()
        self._reorder_columns()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS columns (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    position INTEGER NOT NULL,
                    is_done_column INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    column_id TEXT NOT NULL,
                    FOREIGN KEY (column_id) REFERENCES columns (id)
                )
                """
            )
            conn.commit()

    def _ensure_default_columns(self):
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS cnt FROM columns").fetchone()
            if row["cnt"] > 0:
                return

            default_columns = [
                ("todo", "К выполнению", 0, 0),
                ("in_progress", "В работе", 1, 0),
                ("done", "Готово", 2, 1),
            ]

            conn.executemany(
                """
                INSERT INTO columns (id, name, position, is_done_column)
                VALUES (?, ?, ?, ?)
                """,
                default_columns,
            )
            conn.commit()

    def _reorder_columns(self):
        columns = self.list_columns()
        regular_columns = [c for c in columns if not c.is_done_column]
        done_columns = [c for c in columns if c.is_done_column]
        ordered = regular_columns + done_columns

        with self._connect() as conn:
            for index, column in enumerate(ordered):
                conn.execute(
                    "UPDATE columns SET position = ? WHERE id = ?",
                    (index, column.id),
                )
            conn.commit()

    def list_columns(self):
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, name, position, is_done_column
                FROM columns
                ORDER BY position ASC, name ASC
                """
            ).fetchall()

        return [
            Column(
                id=row["id"],
                name=row["name"],
                position=row["position"],
                is_done_column=bool(row["is_done_column"]),
            )
            for row in rows
        ]

    def get_column(self, column_id: str):
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, name, position, is_done_column
                FROM columns
                WHERE id = ?
                """,
                (column_id,),
            ).fetchone()

        if row is None:
            return None

        return Column(
            id=row["id"],
            name=row["name"],
            position=row["position"],
            is_done_column=bool(row["is_done_column"]),
        )

    def add_column(self, name: str):
        name = name.strip()
        if not name:
            return None

        with self._connect() as conn:
            done_row = conn.execute(
                """
                SELECT id, position
                FROM columns
                WHERE is_done_column = 1
                LIMIT 1
                """
            ).fetchone()

            if done_row is None:
                max_row = conn.execute(
                    "SELECT COALESCE(MAX(position), -1) AS max_pos FROM columns"
                ).fetchone()
                insert_position = max_row["max_pos"] + 1
            else:
                insert_position = done_row["position"]
                conn.execute(
                    """
                    UPDATE columns
                    SET position = position + 1
                    WHERE position >= ?
                    """,
                    (insert_position,),
                )

            column_id = uuid.uuid4().hex
            conn.execute(
                """
                INSERT INTO columns (id, name, position, is_done_column)
                VALUES (?, ?, ?, 0)
                """,
                (column_id, name, insert_position),
            )
            conn.commit()

        self._reorder_columns()
        return self.get_column(column_id)

    def update_column(self, column_id: str, name: str):
        name = name.strip()
        if not name:
            return

        with self._connect() as conn:
            conn.execute(
                """
                UPDATE columns
                SET name = ?
                WHERE id = ?
                """,
                (name, column_id),
            )
            conn.commit()

    def delete_column(self, column_id: str):
        column = self.get_column(column_id)
        if column is None:
            return

        if column.is_done_column:
            return

        with self._connect() as conn:
            task_count = conn.execute(
                "SELECT COUNT(*) AS cnt FROM tasks WHERE column_id = ?",
                (column_id,),
            ).fetchone()["cnt"]

            if task_count > 0:
                return

            conn.execute("DELETE FROM columns WHERE id = ?", (column_id,))
            conn.commit()

        self._reorder_columns()

    def get_tasks_by_column(self, column_id: str):
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, title, column_id
                FROM tasks
                WHERE column_id = ?
                ORDER BY rowid ASC
                """,
                (column_id,),
            ).fetchall()

        return [
            Task(
                id=row["id"],
                title=row["title"],
                column_id=row["column_id"],
            )
            for row in rows
        ]

    def get_task(self, task_id: str):
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, title, column_id
                FROM tasks
                WHERE id = ?
                """,
                (task_id,),
            ).fetchone()

        if row is None:
            return None

        return Task(
            id=row["id"],
            title=row["title"],
            column_id=row["column_id"],
        )

    def add_task(self, title: str, column_id: str):
        title = title.strip()
        if not title:
            return None

        column = self.get_column(column_id)
        if column is None:
            return None

        task_id = uuid.uuid4().hex

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO tasks (id, title, column_id)
                VALUES (?, ?, ?)
                """,
                (task_id, title, column_id),
            )
            conn.commit()

        return self.get_task(task_id)

    def update_task(self, task_id: str, title: str, column_id: str):
        title = title.strip()
        if not title:
            return

        column = self.get_column(column_id)
        if column is None:
            return

        with self._connect() as conn:
            conn.execute(
                """
                UPDATE tasks
                SET title = ?, column_id = ?
                WHERE id = ?
                """,
                (title, column_id, task_id),
            )
            conn.commit()

    def delete_task(self, task_id: str):
        with self._connect() as conn:
            conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()

    def list_tasks(self):
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, title, column_id
                FROM tasks
                ORDER BY rowid ASC
                """
            ).fetchall()

        return [
            Task(
                id=row["id"],
                title=row["title"],
                column_id=row["column_id"],
            )
            for row in rows
        ]
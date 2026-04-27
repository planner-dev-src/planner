from __future__ import annotations

import sqlite3
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Optional


@dataclass
class Workspace:
    id: str
    name: str
    created_at: str


@dataclass
class Column:
    id: str
    workspace_id: str
    name: str
    position: int
    is_done_column: bool
    created_at: str


@dataclass
class Task:
    id: str
    workspace_id: str
    column_id: str
    title: str
    description: str
    priority: str
    due_date: Optional[str]
    created_at: str

    @property
    def priority_label(self) -> str:
        mapping = {
            "low": "Низкий",
            "medium": "Средний",
            "high": "Высокий",
        }
        return mapping.get(self.priority, "Средний")

    def get_due_date_as_date(self) -> Optional[date]:
        if not self.due_date:
            return None
        try:
            return datetime.strptime(self.due_date, "%Y-%m-%d").date()
        except ValueError:
            return None


class Board:
    def __init__(self, db_path: Optional[str] = None):
        base_dir = Path(__file__).resolve().parents[2]
        self.db_path = str(base_dir / "planner.db") if db_path is None else db_path
        self._init_db()
        self._migrate_schema()
        self._ensure_default_workspace()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _now(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _new_id(self) -> str:
        return uuid.uuid4().hex

    def _column_exists(self, conn: sqlite3.Connection, table_name: str, column_name: str) -> bool:
        rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
        return any(row["name"] == column_name for row in rows)

    def _table_exists(self, conn: sqlite3.Connection, table_name: str) -> bool:
        row = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name = ?
            """,
            (table_name,),
        ).fetchone()
        return row is not None

    def _init_db(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS workspaces (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS columns (
                    id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    position INTEGER NOT NULL DEFAULT 0,
                    is_done_column INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                )
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL,
                    column_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    priority TEXT NOT NULL DEFAULT 'medium',
                    due_date TEXT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

            conn.commit()

    def _migrate_schema(self):
        with self._connect() as conn:
            if self._table_exists(conn, "workspaces"):
                if not self._column_exists(conn, "workspaces", "created_at"):
                    conn.execute(
                        "ALTER TABLE workspaces ADD COLUMN created_at TEXT NOT NULL DEFAULT ''"
                    )

            if self._table_exists(conn, "columns"):
                if not self._column_exists(conn, "columns", "workspace_id"):
                    conn.execute(
                        "ALTER TABLE columns ADD COLUMN workspace_id TEXT NOT NULL DEFAULT ''"
                    )
                if not self._column_exists(conn, "columns", "position"):
                    conn.execute(
                        "ALTER TABLE columns ADD COLUMN position INTEGER NOT NULL DEFAULT 0"
                    )
                if not self._column_exists(conn, "columns", "is_done_column"):
                    conn.execute(
                        "ALTER TABLE columns ADD COLUMN is_done_column INTEGER NOT NULL DEFAULT 0"
                    )
                if not self._column_exists(conn, "columns", "created_at"):
                    conn.execute(
                        "ALTER TABLE columns ADD COLUMN created_at TEXT NOT NULL DEFAULT ''"
                    )

            if self._table_exists(conn, "tasks"):
                if not self._column_exists(conn, "tasks", "workspace_id"):
                    conn.execute(
                        "ALTER TABLE tasks ADD COLUMN workspace_id TEXT NOT NULL DEFAULT ''"
                    )
                if not self._column_exists(conn, "tasks", "description"):
                    conn.execute(
                        "ALTER TABLE tasks ADD COLUMN description TEXT NOT NULL DEFAULT ''"
                    )
                if not self._column_exists(conn, "tasks", "priority"):
                    conn.execute(
                        "ALTER TABLE tasks ADD COLUMN priority TEXT NOT NULL DEFAULT 'medium'"
                    )
                if not self._column_exists(conn, "tasks", "due_date"):
                    conn.execute(
                        "ALTER TABLE tasks ADD COLUMN due_date TEXT NULL"
                    )
                if not self._column_exists(conn, "tasks", "created_at"):
                    conn.execute(
                        "ALTER TABLE tasks ADD COLUMN created_at TEXT NOT NULL DEFAULT ''"
                    )

            conn.commit()

            now = self._now()

            if self._table_exists(conn, "workspaces"):
                conn.execute(
                    """
                    UPDATE workspaces
                    SET created_at = ?
                    WHERE created_at IS NULL OR created_at = ''
                    """,
                    (now,),
                )

            first_workspace_row = None
            if self._table_exists(conn, "workspaces"):
                first_workspace_row = conn.execute(
                    "SELECT id FROM workspaces ORDER BY created_at ASC, rowid ASC LIMIT 1"
                ).fetchone()

            first_workspace_id = first_workspace_row["id"] if first_workspace_row else ""

            if self._table_exists(conn, "columns"):
                conn.execute(
                    """
                    UPDATE columns
                    SET created_at = ?
                    WHERE created_at IS NULL OR created_at = ''
                    """,
                    (now,),
                )

                if first_workspace_id:
                    conn.execute(
                        """
                        UPDATE columns
                        SET workspace_id = ?
                        WHERE workspace_id IS NULL OR workspace_id = ''
                        """,
                        (first_workspace_id,),
                    )

                rows = conn.execute(
                    """
                    SELECT id, workspace_id, name, position, is_done_column
                    FROM columns
                    ORDER BY rowid ASC
                    """
                ).fetchall()

                grouped_positions = {}
                for row in rows:
                    workspace_id = row["workspace_id"] or first_workspace_id
                    if not workspace_id:
                        continue
                    grouped_positions.setdefault(workspace_id, [])
                    grouped_positions[workspace_id].append(row)

                for workspace_id, workspace_columns in grouped_positions.items():
                    has_explicit_positions = any((col["position"] or 0) > 0 for col in workspace_columns)
                    if not has_explicit_positions:
                        for index, col in enumerate(workspace_columns):
                            conn.execute(
                                "UPDATE columns SET position = ? WHERE id = ?",
                                (index, col["id"]),
                            )

                done_candidates = conn.execute(
                    """
                    SELECT id, workspace_id, name, is_done_column
                    FROM columns
                    ORDER BY position ASC, rowid ASC
                    """
                ).fetchall()

                workspace_has_done = {}
                for row in done_candidates:
                    if row["is_done_column"]:
                        workspace_has_done[row["workspace_id"]] = True

                for row in done_candidates:
                    workspace_id = row["workspace_id"]
                    if not workspace_id:
                        continue
                    if workspace_has_done.get(workspace_id):
                        continue
                    if (row["name"] or "").strip().lower() == "готово":
                        conn.execute(
                            "UPDATE columns SET is_done_column = 1 WHERE id = ?",
                            (row["id"],),
                        )
                        workspace_has_done[workspace_id] = True

            if self._table_exists(conn, "tasks"):
                conn.execute(
                    """
                    UPDATE tasks
                    SET description = ''
                    WHERE description IS NULL
                    """
                )
                conn.execute(
                    """
                    UPDATE tasks
                    SET priority = 'medium'
                    WHERE priority IS NULL OR priority = ''
                    """
                )
                conn.execute(
                    """
                    UPDATE tasks
                    SET created_at = ?
                    WHERE created_at IS NULL OR created_at = ''
                    """,
                    (now,),
                )

                if first_workspace_id:
                    conn.execute(
                        """
                        UPDATE tasks
                        SET workspace_id = ?
                        WHERE workspace_id IS NULL OR workspace_id = ''
                        """,
                        (first_workspace_id,),
                    )

                task_rows = conn.execute(
                    """
                    SELECT t.id, t.column_id, t.workspace_id, c.workspace_id AS column_workspace_id
                    FROM tasks t
                    LEFT JOIN columns c ON c.id = t.column_id
                    """
                ).fetchall()

                for row in task_rows:
                    target_workspace_id = row["column_workspace_id"] or row["workspace_id"] or first_workspace_id
                    if target_workspace_id and row["workspace_id"] != target_workspace_id:
                        conn.execute(
                            "UPDATE tasks SET workspace_id = ? WHERE id = ?",
                            (target_workspace_id, row["id"]),
                        )

            conn.commit()

    def _workspace_from_row(self, row: sqlite3.Row) -> Workspace:
        return Workspace(
            id=row["id"],
            name=row["name"],
            created_at=row["created_at"],
        )

    def _column_from_row(self, row: sqlite3.Row) -> Column:
        return Column(
            id=row["id"],
            workspace_id=row["workspace_id"],
            name=row["name"],
            position=int(row["position"] or 0),
            is_done_column=bool(row["is_done_column"]),
            created_at=row["created_at"],
        )

    def _task_from_row(self, row: sqlite3.Row) -> Task:
        return Task(
            id=row["id"],
            workspace_id=row["workspace_id"],
            column_id=row["column_id"],
            title=row["title"],
            description=row["description"] or "",
            priority=row["priority"] or "medium",
            due_date=row["due_date"],
            created_at=row["created_at"],
        )

    def _ensure_default_workspace(self):
        workspaces = self.list_workspaces()
        if workspaces:
            for workspace in workspaces:
                self._ensure_done_column(workspace.id)
            return

        workspace = self.add_workspace("Моё направление")
        if workspace is not None:
            self._ensure_done_column(workspace.id)

    def _ensure_done_column(self, workspace_id: str) -> Optional[Column]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM columns
                WHERE workspace_id = ? AND is_done_column = 1
                ORDER BY position ASC, created_at ASC
                LIMIT 1
                """,
                (workspace_id,),
            ).fetchone()

            if row is not None:
                return self._column_from_row(row)

            fallback_row = conn.execute(
                """
                SELECT *
                FROM columns
                WHERE workspace_id = ? AND lower(name) = 'готово'
                ORDER BY position ASC, created_at ASC
                LIMIT 1
                """,
                (workspace_id,),
            ).fetchone()

            if fallback_row is not None:
                conn.execute(
                    "UPDATE columns SET is_done_column = 1 WHERE id = ?",
                    (fallback_row["id"],),
                )
                conn.commit()
                updated = conn.execute(
                    "SELECT * FROM columns WHERE id = ?",
                    (fallback_row["id"],),
                ).fetchone()
                return self._column_from_row(updated)

            next_position = self._get_next_column_position(conn, workspace_id)
            column_id = self._new_id()
            created_at = self._now()

            conn.execute(
                """
                INSERT INTO columns (id, workspace_id, name, position, is_done_column, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (column_id, workspace_id, "Готово", next_position, 1, created_at),
            )
            conn.commit()

            row = conn.execute(
                "SELECT * FROM columns WHERE id = ?",
                (column_id,),
            ).fetchone()
            return self._column_from_row(row)

    def _get_next_column_position(self, conn: sqlite3.Connection, workspace_id: str) -> int:
        row = conn.execute(
            """
            SELECT COALESCE(MAX(position), -1) AS max_position
            FROM columns
            WHERE workspace_id = ?
            """,
            (workspace_id,),
        ).fetchone()
        return int(row["max_position"] or 0) + 1

    def list_workspaces(self) -> list[Workspace]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM workspaces
                ORDER BY created_at ASC, rowid ASC
                """
            ).fetchall()
            return [self._workspace_from_row(row) for row in rows]

    def get_workspace(self, workspace_id: str) -> Optional[Workspace]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM workspaces WHERE id = ?",
                (workspace_id,),
            ).fetchone()
            if row is None:
                return None
            return self._workspace_from_row(row)

    def add_workspace(self, name: str) -> Optional[Workspace]:
        name = (name or "").strip()
        if not name:
            return None

        workspace_id = self._new_id()
        created_at = self._now()

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO workspaces (id, name, created_at)
                VALUES (?, ?, ?)
                """,
                (workspace_id, name, created_at),
            )
            conn.commit()

        self._ensure_done_column(workspace_id)
        return self.get_workspace(workspace_id)

    def update_workspace(self, workspace_id: str, name: str) -> bool:
        name = (name or "").strip()
        if not name:
            return False

        with self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE workspaces
                SET name = ?
                WHERE id = ?
                """,
                (name, workspace_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete_workspace(self, workspace_id: str) -> bool:
        with self._connect() as conn:
            conn.execute("DELETE FROM tasks WHERE workspace_id = ?", (workspace_id,))
            conn.execute("DELETE FROM columns WHERE workspace_id = ?", (workspace_id,))
            cursor = conn.execute("DELETE FROM workspaces WHERE id = ?", (workspace_id,))
            conn.commit()
            return cursor.rowcount > 0

    def list_columns(self, workspace_id: str) -> list[Column]:
        self._ensure_done_column(workspace_id)
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM columns
                WHERE workspace_id = ?
                ORDER BY position ASC, created_at ASC, rowid ASC
                """,
                (workspace_id,),
            ).fetchall()
            return [self._column_from_row(row) for row in rows]

    def get_column(self, column_id: str, workspace_id: Optional[str] = None) -> Optional[Column]:
        with self._connect() as conn:
            if workspace_id:
                row = conn.execute(
                    """
                    SELECT *
                    FROM columns
                    WHERE id = ? AND workspace_id = ?
                    """,
                    (column_id, workspace_id),
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT * FROM columns WHERE id = ?",
                    (column_id,),
                ).fetchone()

            if row is None:
                return None
            return self._column_from_row(row)

    def add_column(self, name: str, workspace_id: str) -> Optional[Column]:
        name = (name or "").strip()
        if not name or not workspace_id:
            return None

        self._ensure_done_column(workspace_id)

        with self._connect() as conn:
            next_position = self._get_next_column_position(conn, workspace_id)
            done_row = conn.execute(
                """
                SELECT id, position
                FROM columns
                WHERE workspace_id = ? AND is_done_column = 1
                LIMIT 1
                """,
                (workspace_id,),
            ).fetchone()

            if done_row is not None:
                done_position = int(done_row["position"] or 0)
                conn.execute(
                    """
                    UPDATE columns
                    SET position = position + 1
                    WHERE workspace_id = ? AND position >= ?
                    """,
                    (workspace_id, done_position),
                )
                insert_position = done_position
            else:
                insert_position = next_position

            column_id = self._new_id()
            created_at = self._now()

            conn.execute(
                """
                INSERT INTO columns (id, workspace_id, name, position, is_done_column, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (column_id, workspace_id, name, insert_position, 0, created_at),
            )
            conn.commit()

            row = conn.execute(
                "SELECT * FROM columns WHERE id = ?",
                (column_id,),
            ).fetchone()
            return self._column_from_row(row) if row else None

    def update_column(self, column_id: str, name: str, workspace_id: Optional[str] = None) -> bool:
        name = (name or "").strip()
        if not name:
            return False

        with self._connect() as conn:
            if workspace_id:
                column_row = conn.execute(
                    """
                    SELECT is_done_column
                    FROM columns
                    WHERE id = ? AND workspace_id = ?
                    """,
                    (column_id, workspace_id),
                ).fetchone()
            else:
                column_row = conn.execute(
                    "SELECT is_done_column FROM columns WHERE id = ?",
                    (column_id,),
                ).fetchone()

            if column_row is None:
                return False

            if bool(column_row["is_done_column"]):
                return False

            if workspace_id:
                cursor = conn.execute(
                    """
                    UPDATE columns
                    SET name = ?
                    WHERE id = ? AND workspace_id = ?
                    """,
                    (name, column_id, workspace_id),
                )
            else:
                cursor = conn.execute(
                    """
                    UPDATE columns
                    SET name = ?
                    WHERE id = ?
                    """,
                    (name, column_id),
                )

            conn.commit()
            return cursor.rowcount > 0

    def delete_column(self, column_id: str, workspace_id: Optional[str] = None) -> bool:
        with self._connect() as conn:
            if workspace_id:
                column_row = conn.execute(
                    """
                    SELECT *
                    FROM columns
                    WHERE id = ? AND workspace_id = ?
                    """,
                    (column_id, workspace_id),
                ).fetchone()
            else:
                column_row = conn.execute(
                    "SELECT * FROM columns WHERE id = ?",
                    (column_id,),
                ).fetchone()

            if column_row is None:
                return False

            if bool(column_row["is_done_column"]):
                return False

            task_count_row = conn.execute(
                "SELECT COUNT(*) AS cnt FROM tasks WHERE column_id = ?",
                (column_id,),
            ).fetchone()
            if int(task_count_row["cnt"] or 0) > 0:
                return False

            if workspace_id:
                cursor = conn.execute(
                    """
                    DELETE FROM columns
                    WHERE id = ? AND workspace_id = ?
                    """,
                    (column_id, workspace_id),
                )
            else:
                cursor = conn.execute(
                    "DELETE FROM columns WHERE id = ?",
                    (column_id,),
                )

            conn.commit()
            return cursor.rowcount > 0

    def list_tasks(self, workspace_id: str) -> list[Task]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM tasks
                WHERE workspace_id = ?
                ORDER BY created_at ASC, rowid ASC
                """,
                (workspace_id,),
            ).fetchall()
            return [self._task_from_row(row) for row in rows]

    def get_tasks_by_column(self, column_id: str, workspace_id: Optional[str] = None) -> list[Task]:
        with self._connect() as conn:
            if workspace_id:
                rows = conn.execute(
                    """
                    SELECT *
                    FROM tasks
                    WHERE column_id = ? AND workspace_id = ?
                    ORDER BY created_at ASC, rowid ASC
                    """,
                    (column_id, workspace_id),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT *
                    FROM tasks
                    WHERE column_id = ?
                    ORDER BY created_at ASC, rowid ASC
                    """,
                    (column_id,),
                ).fetchall()

            return [self._task_from_row(row) for row in rows]

    def get_task(self, task_id: str, workspace_id: Optional[str] = None) -> Optional[Task]:
        with self._connect() as conn:
            if workspace_id:
                row = conn.execute(
                    """
                    SELECT *
                    FROM tasks
                    WHERE id = ? AND workspace_id = ?
                    """,
                    (task_id, workspace_id),
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT * FROM tasks WHERE id = ?",
                    (task_id,),
                ).fetchone()

            if row is None:
                return None
            return self._task_from_row(row)

    def add_task(
        self,
        title: str,
        description: str,
        priority: str,
        due_date: Optional[date],
        column_id: str,
        workspace_id: str,
    ) -> Optional[Task]:
        title = (title or "").strip()
        description = (description or "").strip()
        priority = (priority or "medium").strip()

        if not title or not column_id or not workspace_id:
            return None

        if priority not in {"low", "medium", "high"}:
            priority = "medium"

        due_date_str = due_date.isoformat() if due_date else None

        with self._connect() as conn:
            column_row = conn.execute(
                """
                SELECT id
                FROM columns
                WHERE id = ? AND workspace_id = ?
                """,
                (column_id, workspace_id),
            ).fetchone()
            if column_row is None:
                return None

            task_id = self._new_id()
            created_at = self._now()

            conn.execute(
                """
                INSERT INTO tasks (id, workspace_id, column_id, title, description, priority, due_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (task_id, workspace_id, column_id, title, description, priority, due_date_str, created_at),
            )
            conn.commit()

            row = conn.execute(
                "SELECT * FROM tasks WHERE id = ?",
                (task_id,),
            ).fetchone()
            return self._task_from_row(row) if row else None

    def update_task(
        self,
        task_id: str,
        title: str,
        description: str,
        priority: str,
        due_date: Optional[date],
        column_id: str,
        workspace_id: str,
    ) -> bool:
        title = (title or "").strip()
        description = (description or "").strip()
        priority = (priority or "medium").strip()

        if not title or not task_id or not column_id or not workspace_id:
            return False

        if priority not in {"low", "medium", "high"}:
            priority = "medium"

        due_date_str = due_date.isoformat() if due_date else None

        with self._connect() as conn:
            column_row = conn.execute(
                """
                SELECT id
                FROM columns
                WHERE id = ? AND workspace_id = ?
                """,
                (column_id, workspace_id),
            ).fetchone()
            if column_row is None:
                return False

            cursor = conn.execute(
                """
                UPDATE tasks
                SET title = ?, description = ?, priority = ?, due_date = ?, column_id = ?, workspace_id = ?
                WHERE id = ? AND workspace_id = ?
                """,
                (title, description, priority, due_date_str, column_id, workspace_id, task_id, workspace_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete_task(self, task_id: str, workspace_id: Optional[str] = None) -> bool:
        with self._connect() as conn:
            if workspace_id:
                cursor = conn.execute(
                    """
                    DELETE FROM tasks
                    WHERE id = ? AND workspace_id = ?
                    """,
                    (task_id, workspace_id),
                )
            else:
                cursor = conn.execute(
                    "DELETE FROM tasks WHERE id = ?",
                    (task_id,),
                )

            conn.commit()
            return cursor.rowcount > 0
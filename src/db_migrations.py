from __future__ import annotations

from src.db import get_db


def _table_columns(table_name: str) -> set[str]:
    db = get_db()
    rows = db.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {row["name"] for row in rows}


def _table_exists(table_name: str) -> bool:
    db = get_db()
    row = db.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name = ?
        """,
        (table_name,),
    ).fetchone()
    return row is not None


def migrate_programs_table() -> None:
    db = get_db()

    if not _table_exists("programs"):
        return

    columns = _table_columns("programs")

    if "status" not in columns:
        db.execute(
            """
            ALTER TABLE programs
            ADD COLUMN status TEXT NOT NULL DEFAULT 'active'
            """
        )

    columns = _table_columns("programs")

    if "updated_at" not in columns:
        db.execute(
            """
            ALTER TABLE programs
            ADD COLUMN updated_at TEXT
            """
        )

    columns = _table_columns("programs")

    if "created_at" in columns and "updated_at" in columns:
        db.execute(
            """
            UPDATE programs
            SET updated_at = created_at
            WHERE updated_at IS NULL
            """
        )

    db.commit()


def migrate_projects_table() -> None:
    db = get_db()

    if not _table_exists("projects"):
        return

    columns = _table_columns("projects")

    if "status" not in columns:
        db.execute(
            """
            ALTER TABLE projects
            ADD COLUMN status TEXT NOT NULL DEFAULT 'active'
            """
        )

    columns = _table_columns("projects")

    if "program_id" not in columns:
        db.execute(
            """
            ALTER TABLE projects
            ADD COLUMN program_id TEXT
            """
        )

    db.commit()


def run_migrations() -> None:
    migrate_programs_table()
    migrate_projects_table()
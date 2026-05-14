from __future__ import annotations

from sqlalchemy import text

from src.extensions import db


def _get_column_names(table_name: str) -> set[str]:
    rows = db.session.execute(text(f"PRAGMA table_info({table_name})")).mappings().all()
    return {row["name"] for row in rows}


def _ensure_workspaces_columns() -> None:
    table_names = set(db.inspect(db.engine).get_table_names())
    if "workspaces" not in table_names:
        return

    columns = _get_column_names("workspaces")

    statements: list[str] = []

    if "is_default" not in columns:
        statements.append(
            "ALTER TABLE workspaces ADD COLUMN is_default BOOLEAN NOT NULL DEFAULT 0"
        )

    if "created_at" not in columns:
        statements.append(
            "ALTER TABLE workspaces ADD COLUMN created_at DATETIME"
        )

    if "updated_at" not in columns:
        statements.append(
            "ALTER TABLE workspaces ADD COLUMN updated_at DATETIME"
        )

    for statement in statements:
        db.session.execute(text(statement))

    if statements:
        db.session.execute(
            text(
                """
                UPDATE workspaces
                SET is_default = 1
                WHERE id = (
                    SELECT id
                    FROM workspaces
                    ORDER BY rowid ASC
                    LIMIT 1
                )
                AND NOT EXISTS (
                    SELECT 1
                    FROM workspaces
                    WHERE is_default = 1
                )
                """
            )
        )

        db.session.execute(
            text(
                """
                UPDATE workspaces
                SET created_at = COALESCE(created_at, CURRENT_TIMESTAMP),
                    updated_at = COALESCE(updated_at, CURRENT_TIMESTAMP)
                """
            )
        )

        db.session.commit()


def init_db(app) -> None:
    with app.app_context():
        db.create_all()
        _ensure_workspaces_columns()
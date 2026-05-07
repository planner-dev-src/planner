# src/db.py
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from flask import current_app, g


def _default_db_path() -> str:
    # planner.db в корне проекта (на уровень выше src/)
    base_dir = Path(__file__).resolve().parents[1]
    return str(base_dir / "planner.db")


def get_db() -> sqlite3.Connection:
    """
    Возвращает соединение с БД для текущего app/request контекста.
    Соединение кешируется в flask.g.
    """
    if "db" not in g:
        db_path = current_app.config.get("DATABASE", _default_db_path())
        conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        conn.row_factory = sqlite3.Row
        g.db = conn
    return g.db


def close_db(e=None) -> None:
    """
    Закрыть соединение в конце request/app контекста.
    """
    db = g.pop("db", None)
    if db is not None:
        db.close()


def now_iso() -> str:
    """
    Текущее время в ISO‑формате (UTC) для created_at/updated_at.
    """
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
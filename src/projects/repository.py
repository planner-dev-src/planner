from __future__ import annotations

from datetime import datetime
from typing import Iterable, List, Optional

from src.db import get_db, now_iso
from .models import Project


class ProjectRepository:
    @staticmethod
    def _row_to_project(row) -> Project:
        data = dict(row)
        created_at_raw = data.get("created_at")
        created_at = (
            datetime.fromisoformat(created_at_raw)
            if isinstance(created_at_raw, str)
            else created_at_raw
        )

        return Project(
            id=data["id"],
            title=data["title"],
            description=data.get("description") or "",
            parent_id=data.get("parent_id"),
            program_id=data.get("program_id"),
            status=data.get("status") or "active",
            created_at=created_at,
        )

    @classmethod
    def get(cls, project_id: int) -> Optional[Project]:
        db = get_db()
        row = db.execute(
            "SELECT * FROM projects WHERE id = ?",
            (project_id,),
        ).fetchone()
        return cls._row_to_project(row) if row else None

    @classmethod
    def list_for_program(cls, program_id: str) -> List[Project]:
        db = get_db()
        rows = db.execute(
            """
            SELECT *
            FROM projects
            WHERE program_id = ?
              AND status = 'active'
            ORDER BY created_at DESC, id DESC
            """,
            (program_id,),
        ).fetchall()
        return [cls._row_to_project(r) for r in rows]

    @classmethod
    def list_root(cls, archived: bool = False) -> List[Project]:
        db = get_db()
        status = "archived" if archived else "active"
        rows = db.execute(
            """
            SELECT *
            FROM projects
            WHERE parent_id IS NULL
              AND status = ?
            ORDER BY created_at DESC, id DESC
            """,
            (status,),
        ).fetchall()
        return [cls._row_to_project(r) for r in rows]

    @classmethod
    def list_children(cls, parent_id: int) -> List[Project]:
        db = get_db()
        rows = db.execute(
            """
            SELECT *
            FROM projects
            WHERE parent_id = ?
            ORDER BY created_at ASC, id ASC
            """,
            (parent_id,),
        ).fetchall()
        return [cls._row_to_project(r) for r in rows]

    @classmethod
    def list_many(cls, ids: Iterable[int]) -> List[Project]:
        ids = list(ids)
        if not ids:
            return []
        placeholders = ",".join("?" for _ in ids)
        db = get_db()
        rows = db.execute(
            f"SELECT * FROM projects WHERE id IN ({placeholders})",
            tuple(ids),
        ).fetchall()
        return [cls._row_to_project(r) for r in rows]

    @classmethod
    def create(
        cls,
        title: str,
        description: str = "",
        parent_id: Optional[int] = None,
        program_id: Optional[str] = None,
        status: str = "active",
    ) -> Project:
        db = get_db()
        now = now_iso()
        cur = db.execute(
            """
            INSERT INTO projects (
                title,
                description,
                parent_id,
                program_id,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (title, description, parent_id, program_id, status, now),
        )
        db.commit()
        new_id = cur.lastrowid
        row = db.execute(
            "SELECT * FROM projects WHERE id = ?",
            (new_id,),
        ).fetchone()
        return cls._row_to_project(row)

    @classmethod
    def update_status(cls, project_id: int, status: str) -> None:
        db = get_db()
        db.execute(
            "UPDATE projects SET status = ? WHERE id = ?",
            (status, project_id),
        )
        db.commit()
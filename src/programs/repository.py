from __future__ import annotations

from typing import List, Optional

from src.db import get_db, now_iso
from .models import Program


class ProgramRepository:
    @staticmethod
    def _row_to_program(row) -> Program:
        data = dict(row)
        return Program(
            id=data["id"],
            title=data["title"],
            owner_id=data["owner_id"],
            note_html=data.get("note_html") or "",
            note_raw=data.get("note_raw") or "",
            status=data.get("status") or "active",
        )

    @classmethod
    def save(cls, program: Program) -> None:
        db = get_db()
        now = now_iso()
        db.execute(
            """
            INSERT INTO programs (
                id,
                title,
                owner_id,
                note_html,
                note_raw,
                status,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                program.id,
                program.title,
                program.owner_id,
                program.note_html,
                program.note_raw,
                program.status,
                now,
                now,
            ),
        )
        db.commit()

    @classmethod
    def update(
        cls,
        program_id: str,
        owner_id: str,
        title: str,
        note_raw: str,
        note_html: str,
    ) -> bool:
        db = get_db()
        cur = db.execute(
            """
            UPDATE programs
            SET title = ?,
                note_raw = ?,
                note_html = ?,
                updated_at = ?
            WHERE id = ?
              AND owner_id = ?
            """,
            (
                title,
                note_raw,
                note_html,
                now_iso(),
                program_id,
                owner_id,
            ),
        )
        db.commit()
        return cur.rowcount > 0

    @classmethod
    def list_all_for_user(cls, owner_id: str) -> List[Program]:
        db = get_db()
        rows = db.execute(
            """
            SELECT *
            FROM programs
            WHERE owner_id = ?
            ORDER BY created_at DESC, id DESC
            """,
            (owner_id,),
        ).fetchall()
        return [cls._row_to_program(row) for row in rows]

    @classmethod
    def list_active_for_user(cls, owner_id: str) -> List[Program]:
        db = get_db()
        rows = db.execute(
            """
            SELECT *
            FROM programs
            WHERE owner_id = ?
              AND status = 'active'
            ORDER BY created_at DESC, id DESC
            """,
            (owner_id,),
        ).fetchall()
        return [cls._row_to_program(row) for row in rows]

    @classmethod
    def list_archived_for_user(cls, owner_id: str) -> List[Program]:
        db = get_db()
        rows = db.execute(
            """
            SELECT *
            FROM programs
            WHERE owner_id = ?
              AND status = 'archived'
            ORDER BY updated_at DESC, id DESC
            """,
            (owner_id,),
        ).fetchall()
        return [cls._row_to_program(row) for row in rows]

    @classmethod
    def get_by_id(cls, program_id: str) -> Optional[Program]:
        db = get_db()
        row = db.execute(
            """
            SELECT *
            FROM programs
            WHERE id = ?
            """,
            (program_id,),
        ).fetchone()
        return cls._row_to_program(row) if row else None

    @classmethod
    def get_by_id_for_user(cls, program_id: str, owner_id: str) -> Optional[Program]:
        db = get_db()
        row = db.execute(
            """
            SELECT *
            FROM programs
            WHERE id = ?
              AND owner_id = ?
            """,
            (program_id, owner_id),
        ).fetchone()
        return cls._row_to_program(row) if row else None

    @classmethod
    def archive(cls, program_id: str, owner_id: str) -> bool:
        db = get_db()
        cur = db.execute(
            """
            UPDATE programs
            SET status = 'archived',
                updated_at = ?
            WHERE id = ?
              AND owner_id = ?
            """,
            (now_iso(), program_id, owner_id),
        )
        db.commit()
        return cur.rowcount > 0

    @classmethod
    def unarchive(cls, program_id: str, owner_id: str) -> bool:
        db = get_db()
        cur = db.execute(
            """
            UPDATE programs
            SET status = 'active',
                updated_at = ?
            WHERE id = ?
              AND owner_id = ?
            """,
            (now_iso(), program_id, owner_id),
        )
        db.commit()
        return cur.rowcount > 0
# src/programs/attachments_repository.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
from uuid import uuid4

from src.db import get_db, now_iso


@dataclass
class ProgramAttachment:
    id: str
    program_id: str
    kind: str
    filename: str
    stored_path: str
    content_type: Optional[str]
    uploaded_by: str
    uploaded_at: str


class ProgramAttachmentRepository:
    @staticmethod
    def _row_to_attachment(row) -> ProgramAttachment:
        data = dict(row)
        return ProgramAttachment(
            id=data["id"],
            program_id=data["program_id"],
            kind=data["kind"],
            filename=data["filename"],
            stored_path=data["stored_path"],
            content_type=data.get("content_type"),
            uploaded_by=data["uploaded_by"],
            uploaded_at=data["uploaded_at"],
        )

    @classmethod
    def list_for_program(cls, program_id: str) -> List[ProgramAttachment]:
        db = get_db()
        rows = db.execute(
            """
            SELECT *
            FROM program_attachments
            WHERE program_id = ?
            ORDER BY uploaded_at DESC
            """,
            (program_id,),
        ).fetchall()
        return [cls._row_to_attachment(r) for r in rows]

    @classmethod
    def add(
        cls,
        program_id: str,
        kind: str,
        filename: str,
        stored_path: str,
        content_type: Optional[str],
        uploaded_by: str,
    ) -> ProgramAttachment:
        db = get_db()
        att = ProgramAttachment(
            id=uuid4().hex,
            program_id=program_id,
            kind=kind,
            filename=filename,
            stored_path=stored_path,
            content_type=content_type,
            uploaded_by=uploaded_by,
            uploaded_at=now_iso(),
        )
        db.execute(
            """
            INSERT INTO program_attachments (
                id, program_id, kind, filename,
                stored_path, content_type,
                uploaded_by, uploaded_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                att.id,
                att.program_id,
                att.kind,
                att.filename,
                att.stored_path,
                att.content_type,
                att.uploaded_by,
                att.uploaded_at,
            ),
        )
        db.commit()
        return att

    @classmethod
    def get(cls, attachment_id: str) -> Optional[ProgramAttachment]:
        db = get_db()
        row = db.execute(
            "SELECT * FROM program_attachments WHERE id = ?",
            (attachment_id,),
        ).fetchone()
        return cls._row_to_attachment(row) if row else None
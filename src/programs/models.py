from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4


@dataclass
class Program:
    id: str
    title: str
    owner_id: str
    note_html: str = ""
    note_raw: str = ""
    status: str = "active"


def new_program(
    title: str,
    owner_id: str,
    note_html: str = "",
    note_raw: str = "",
) -> Program:
    return Program(
        id=str(uuid4()),
        title=title.strip(),
        owner_id=owner_id,
        note_html=note_html or "",
        note_raw=note_raw or "",
        status="active",
    )
from __future__ import annotations

from src.extensions import db
from .models import Workspace


class WorkspaceRepository:
    def get_by_id(self, workspace_id: str) -> Workspace | None:
        if not workspace_id:
            return None
        return db.session.get(Workspace, workspace_id)

    def get_default(self) -> Workspace | None:
        return (
            Workspace.query
            .filter_by(is_default=True)
            .order_by(Workspace.created_at.asc())
            .first()
        )

    def get_first(self) -> Workspace | None:
        return Workspace.query.order_by(Workspace.created_at.asc()).first()

    def list_all(self) -> list[Workspace]:
        return Workspace.query.order_by(Workspace.created_at.asc()).all()

    def create(self, *, name: str, is_default: bool = False) -> Workspace:
        workspace = Workspace(name=name.strip(), is_default=is_default)
        db.session.add(workspace)
        db.session.commit()
        return workspace

    def save(self, workspace: Workspace) -> Workspace:
        db.session.add(workspace)
        db.session.commit()
        return workspace

    def unset_default_for_all(self) -> None:
        Workspace.query.update({"is_default": False})
        db.session.commit()
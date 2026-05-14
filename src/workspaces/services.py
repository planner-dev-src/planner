from __future__ import annotations

from .models import Workspace
from .repository import WorkspaceRepository


class WorkspaceService:
    def __init__(self, repository: WorkspaceRepository | None = None) -> None:
        self.repository = repository or WorkspaceRepository()

    def get_workspace(self, workspace_id: str) -> Workspace | None:
        return self.repository.get_by_id(workspace_id)

    def list_workspaces(self) -> list[Workspace]:
        return self.repository.list_all()

    def create_workspace(self, *, name: str, is_default: bool = False) -> Workspace:
        normalized_name = (name or "").strip()
        if not normalized_name:
            raise ValueError("Название workspace не может быть пустым.")

        if is_default:
            self.repository.unset_default_for_all()

        return self.repository.create(name=normalized_name, is_default=is_default)

    def ensure_default_workspace(self) -> Workspace:
        default_workspace = self.repository.get_default()
        if default_workspace is not None:
            return default_workspace

        first_workspace = self.repository.get_first()
        if first_workspace is not None:
            first_workspace.is_default = True
            return self.repository.save(first_workspace)

        return self.repository.create(name="Личный", is_default=True)

    def get_or_create_current_workspace(self) -> Workspace:
        return self.ensure_default_workspace()

    def set_default_workspace(self, workspace_id: str) -> Workspace:
        workspace = self.repository.get_by_id(workspace_id)
        if workspace is None:
            raise ValueError("Workspace не найден.")

        self.repository.unset_default_for_all()
        workspace.is_default = True
        return self.repository.save(workspace)


service = WorkspaceService()


def get_or_create_current_workspace() -> Workspace:
    return service.get_or_create_current_workspace()
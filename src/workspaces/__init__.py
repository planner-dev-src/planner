from flask import Blueprint


workspaces_bp = Blueprint(
    "workspaces",
    __name__,
    url_prefix="/workspaces",
)

from .models import Workspace
from .repository import WorkspaceRepository
from .services import WorkspaceService, get_or_create_current_workspace, service
from . import routes  # noqa: E402,F401

__all__ = [
    "workspaces_bp",
    "Workspace",
    "WorkspaceRepository",
    "WorkspaceService",
    "service",
    "get_or_create_current_workspace",
]
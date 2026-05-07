from __future__ import annotations

from typing import Optional

from src.programs.repository import ProgramRepository
from .repository import ProjectRepository


PROJECT_STATUS_ACTIVE = "active"
PROJECT_STATUS_ARCHIVED = "archived"
ALLOWED_PROJECT_STATUSES = {
    PROJECT_STATUS_ACTIVE,
    PROJECT_STATUS_ARCHIVED,
}


def get_project(project_id: int):
    return ProjectRepository.get(project_id)


def list_root_projects(include_archived: bool = False):
    if include_archived:
        active_projects = ProjectRepository.list_root(archived=False)
        archived_projects = ProjectRepository.list_root(archived=True)
        return active_projects + archived_projects
    return ProjectRepository.list_root(archived=False)


def list_archived_root_projects():
    return ProjectRepository.list_root(archived=True)


def list_child_projects(parent_id: int, include_archived: bool = True):
    projects = ProjectRepository.list_children(parent_id)
    if include_archived:
        return projects
    return [project for project in projects if project.status == PROJECT_STATUS_ACTIVE]


def list_projects(include_archived: bool = True):
    result = []

    active_roots = ProjectRepository.list_root(archived=False)
    archived_roots = ProjectRepository.list_root(archived=True) if include_archived else []

    def walk(project):
        result.append(project)
        for child in ProjectRepository.list_children(project.id):
            if include_archived or child.status == PROJECT_STATUS_ACTIVE:
                walk(child)

    for root in active_roots:
        walk(root)

    for root in archived_roots:
        walk(root)

    return result


def create_project(
    title: str,
    description: str = "",
    parent_id: Optional[int] = None,
    program_id: Optional[str] = None,
):
    title = (title or "").strip()
    description = (description or "").strip()
    program_id = (program_id or "").strip() or None

    if not title:
        raise ValueError("Название проекта обязательно.")

    if parent_id is not None:
        parent_project = ProjectRepository.get(parent_id)
        if parent_project is None:
            raise ValueError("Родительский проект не найден.")
        if parent_project.status != PROJECT_STATUS_ACTIVE:
            raise ValueError("Нельзя создавать дочерний проект внутри архивного проекта.")

    if program_id is not None:
        program = ProgramRepository.get_by_id(program_id)
        if program is None:
            raise ValueError("Программа не найдена.")
        if getattr(program, "status", "active") != "active":
            raise ValueError("Нельзя создавать проект внутри архивной программы.")

    return ProjectRepository.create(
        title=title,
        description=description,
        parent_id=parent_id,
        program_id=program_id,
        status=PROJECT_STATUS_ACTIVE,
    )


def update_project(project_id: int, title: str, description: str = ""):
    project = ProjectRepository.get(project_id)
    if project is None:
        raise ValueError("Проект не найден.")

    if project.status != PROJECT_STATUS_ACTIVE:
        raise ValueError("Можно редактировать только активный проект.")

    title = (title or "").strip()
    description = (description or "").strip()

    if not title:
        raise ValueError("Название проекта обязательно.")

    return _update_project_full(
        project_id=project.id,
        title=title,
        description=description,
        parent_id=project.parent_id,
        status=project.status,
    )


def _collect_descendant_ids(project_id: int):
    descendants = []
    children = ProjectRepository.list_children(project_id)

    for child in children:
        descendants.append(child.id)
        descendants.extend(_collect_descendant_ids(child.id))

    return descendants


def list_possible_parents(project_id: int):
    excluded_ids = {project_id, *_collect_descendant_ids(project_id)}

    return [
        project
        for project in list_projects(include_archived=False)
        if project.id not in excluded_ids and project.status == PROJECT_STATUS_ACTIVE
    ]


def _update_project_full(
    project_id: int,
    title: str,
    description: str,
    parent_id: Optional[int],
    status: str,
):
    project = ProjectRepository.get(project_id)
    if project is None:
        return None

    if status not in ALLOWED_PROJECT_STATUSES:
        raise ValueError("Передан недопустимый статус проекта.")

    from src.db import get_db

    conn = get_db()
    conn.execute(
        """
        UPDATE projects
        SET title = ?, description = ?, parent_id = ?, status = ?
        WHERE id = ?
        """,
        (title, description, parent_id, status, project_id),
    )
    conn.commit()
    return ProjectRepository.get(project_id)


def _delete_project(project_id: int):
    from src.db import get_db

    conn = get_db()
    cur = conn.execute(
        "DELETE FROM projects WHERE id = ?",
        (project_id,),
    )
    conn.commit()
    return cur.rowcount > 0


def move_project(project_id: int, new_parent_id: Optional[int]):
    project = ProjectRepository.get(project_id)
    if project is None:
        raise ValueError("Проект не найден.")

    if project.status != PROJECT_STATUS_ACTIVE:
        raise ValueError("Можно переносить только активные проекты.")

    if new_parent_id == project_id:
        raise ValueError("Нельзя сделать проект родителем самого себя.")

    if new_parent_id is not None:
        possible_parent_ids = {item.id for item in list_possible_parents(project_id)}
        if new_parent_id not in possible_parent_ids:
            raise ValueError("Нельзя перенести проект в выбранный родительский проект.")

    updated_project = _update_project_full(
        project_id,
        title=project.title,
        description=project.description,
        parent_id=new_parent_id,
        status=project.status,
    )
    return updated_project


def attach_existing_project(parent_project_id: int, child_project_id: int):
    parent_project = ProjectRepository.get(parent_project_id)
    if parent_project is None:
        raise ValueError("Родительский проект не найден.")

    child_project = ProjectRepository.get(child_project_id)
    if child_project is None:
        raise ValueError("Встраиваемый проект не найден.")

    if parent_project.status != PROJECT_STATUS_ACTIVE:
        raise ValueError("Нельзя встраивать проект в архивный проект.")

    if child_project.status != PROJECT_STATUS_ACTIVE:
        raise ValueError("Можно встраивать только активный проект.")

    if parent_project_id == child_project_id:
        raise ValueError("Нельзя встроить проект в самого себя.")

    possible_parent_ids = {item.id for item in list_possible_parents(child_project_id)}
    if parent_project_id not in possible_parent_ids:
        raise ValueError("Нельзя встроить проект в выбранное место.")

    updated_child = _update_project_full(
        child_project_id,
        title=child_project.title,
        description=child_project.description,
        parent_id=parent_project_id,
        status=child_project.status,
    )
    return updated_child


def list_projects_for_clone_choice():
    return [
        (project.id, project.title)
        for project in list_projects(include_archived=False)
        if project.status == PROJECT_STATUS_ACTIVE
    ]


def _build_project_subtree(project_id: int):
    project = ProjectRepository.get(project_id)
    if project is None:
        raise ValueError("Проект не найден.")

    node = {
        "id": project.id,
        "title": project.title,
        "description": project.description,
        "status": project.status,
        "created_at": project.created_at,
        "children": [],
    }

    children = ProjectRepository.list_children(project_id)
    node["children"] = [
        _build_project_subtree(child.id)
        for child in children
    ]
    return node


def build_project_tree(project_id: int):
    return _build_project_subtree(project_id)


def _clone_subtree(node, new_parent_id=None, root_title=None):
    new_title = root_title if root_title is not None else node["title"]

    cloned_project = ProjectRepository.create(
        title=new_title,
        description=node.get("description", ""),
        parent_id=new_parent_id,
        program_id=None,
        status=PROJECT_STATUS_ACTIVE,
    )

    for child in node.get("children", []):
        _clone_subtree(
            child,
            new_parent_id=cloned_project.id,
            root_title=None,
        )

    return cloned_project


def clone_project_tree(source_project_id: int, new_root_title: str):
    source_project = ProjectRepository.get(source_project_id)
    if source_project is None:
        raise ValueError("Исходный проект не найден.")
    if source_project.status != PROJECT_STATUS_ACTIVE:
        raise ValueError("Клонировать можно только активный проект.")

    source_tree = _build_project_subtree(source_project_id)
    new_root_title = (new_root_title or "").strip()

    if not new_root_title:
        raise ValueError("Название новой корневой копии обязательно.")

    return _clone_subtree(
        source_tree,
        new_parent_id=None,
        root_title=new_root_title,
    )


def archive_project(project_id: int):
    project = ProjectRepository.get(project_id)
    if project is None:
        raise ValueError("Проект не найден.")

    if project.status == PROJECT_STATUS_ARCHIVED:
        raise ValueError("Проект уже находится в архиве.")

    updated_project = _update_project_full(
        project_id,
        title=project.title,
        description=project.description,
        parent_id=project.parent_id,
        status=PROJECT_STATUS_ARCHIVED,
    )
    return updated_project


def restore_project(project_id: int):
    project = ProjectRepository.get(project_id)
    if project is None:
        raise ValueError("Проект не найден.")

    if project.status == PROJECT_STATUS_ACTIVE:
        raise ValueError("Проект уже активен.")

    if project.parent_id is not None:
        parent_project = ProjectRepository.get(project.parent_id)
        if parent_project is None:
            raise ValueError("Невозможно восстановить проект: родительский проект не найден.")
        if parent_project.status != PROJECT_STATUS_ACTIVE:
            raise ValueError("Нельзя восстановить проект, пока его родитель находится в архиве.")

    updated_project = _update_project_full(
        project_id,
        title=project.title,
        description=project.description,
        parent_id=project.parent_id,
        status=PROJECT_STATUS_ACTIVE,
    )
    return updated_project


def can_delete_project(project_id: int):
    project = ProjectRepository.get(project_id)
    if project is None:
        raise ValueError("Проект не найден.")

    children = ProjectRepository.list_children(project_id)
    descendants_count = len(_collect_descendant_ids(project_id))

    return {
        "project": project,
        "is_archived": project.status == PROJECT_STATUS_ARCHIVED,
        "has_children": len(children) > 0,
        "children_count": len(children),
        "descendants_count": descendants_count,
        "can_delete_directly": (
            project.status == PROJECT_STATUS_ARCHIVED and len(children) == 0
        ),
        "can_delete_with_descendants": (
            project.status == PROJECT_STATUS_ARCHIVED and len(children) > 0
        ),
    }


def _delete_project_subtree(project_id: int):
    children = ProjectRepository.list_children(project_id)
    for child in children:
        _delete_project_subtree(child.id)
    _delete_project(child.id if False else project_id)


def delete_project_with_policy(project_id: int, delete_descendants: bool = False):
    project = ProjectRepository.get(project_id)
    if project is None:
        raise ValueError("Проект не найден.")

    if project.status != PROJECT_STATUS_ARCHIVED:
        raise ValueError("Удалять можно только архивный проект.")

    children = ProjectRepository.list_children(project_id)
    if children and not delete_descendants:
        raise ValueError(
            "У проекта есть вложенные элементы. Подтвердите удаление вложенных элементов."
        )

    if children and delete_descendants:
        _delete_project_subtree(project_id)
        return

    deleted = _delete_project(project_id)
    if not deleted:
        raise ValueError("Не удалось удалить проект.")
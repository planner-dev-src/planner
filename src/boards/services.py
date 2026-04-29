from dataclasses import dataclass
from typing import Optional


@dataclass
class ServiceResult:
    ok: bool
    message: str
    category: str = "success"
    workspace_id: Optional[str] = None
    edit_workspace_id: Optional[str] = None
    edit_column_id: Optional[str] = None
    edit_task_id: Optional[str] = None


def _result(
    ok: bool,
    message: str,
    category: str = "success",
    workspace_id: Optional[str] = None,
    edit_workspace_id: Optional[str] = None,
    edit_column_id: Optional[str] = None,
    edit_task_id: Optional[str] = None,
) -> ServiceResult:
    return ServiceResult(
        ok=ok,
        message=message,
        category=category,
        workspace_id=workspace_id,
        edit_workspace_id=edit_workspace_id,
        edit_column_id=edit_column_id,
        edit_task_id=edit_task_id,
    )


def create_workspace(board, name: str) -> ServiceResult:
    workspace = board.add_workspace(name.strip())
    if workspace is None:
        return _result(False, "Не удалось создать направление.", "error")
    return _result(True, "Направление создано.", "success", workspace_id=workspace.id)


def rename_workspace(board, workspace_id: str, name: str) -> ServiceResult:
    workspace = board.get_workspace(workspace_id)
    if workspace is None:
        return _result(False, "Направление не найдено.", "error")

    board.update_workspace(workspace_id, name.strip())
    return _result(True, "Направление переименовано.", "success", workspace_id=workspace_id)


def remove_workspace(board, workspace_id: str) -> ServiceResult:
    workspace = board.get_workspace(workspace_id)
    if workspace is None:
        return _result(False, "Направление не найдено.", "error")

    columns = board.list_columns(workspace_id)
    tasks = board.list_tasks(workspace_id)

    has_tasks = len(tasks) > 0
    user_columns_count = sum(1 for column in columns if not column.is_done_column)

    if has_tasks and user_columns_count > 0:
        return _result(
            False,
            "Сначала удалите все задачи и пользовательские колонки.",
            "error",
            workspace_id=workspace_id,
        )
    if has_tasks:
        return _result(
            False,
            "Сначала удалите все задачи в этом направлении.",
            "error",
            workspace_id=workspace_id,
        )
    if user_columns_count > 0:
        return _result(
            False,
            "Сначала удалите все пользовательские колонки. Системная колонка «Готово» удалится вместе с направлением.",
            "error",
            workspace_id=workspace_id,
        )

    board.delete_workspace(workspace_id)
    return _result(True, "Направление удалено.", "success")


def create_column(board, workspace_id: str, name: str) -> ServiceResult:
    workspace = board.get_workspace(workspace_id)
    if workspace is None:
        return _result(False, "Направление не найдено.", "error")

    column = board.add_column(name.strip(), workspace_id=workspace_id)
    if column is None:
        return _result(False, "Не удалось создать колонку.", "error", workspace_id=workspace_id)

    return _result(True, "Колонка добавлена.", "success", workspace_id=workspace_id)


def rename_column(board, workspace_id: str, column_id: str, name: str) -> ServiceResult:
    column = board.get_column(column_id, workspace_id=workspace_id)
    if column is None:
        return _result(False, "Колонка не найдена.", "error", workspace_id=workspace_id)

    if getattr(column, "is_done_column", False):
        return _result(
            False,
            "Системную колонку «Готово» нельзя переименовать.",
            "error",
            workspace_id=workspace_id,
        )

    board.update_column(column_id, name.strip(), workspace_id=workspace_id)
    return _result(True, "Колонка переименована.", "success", workspace_id=workspace_id)


def remove_column(board, workspace_id: str, column_id: str) -> ServiceResult:
    column = board.get_column(column_id, workspace_id=workspace_id)
    if column is None:
        return _result(False, "Колонка не найдена.", "error", workspace_id=workspace_id)

    if getattr(column, "is_done_column", False):
        return _result(
            False,
            "Системную колонку «Готово» нельзя удалить отдельно.",
            "error",
            workspace_id=workspace_id,
        )

    tasks = board.get_tasks_by_column(column_id, workspace_id=workspace_id)
    if tasks:
        return _result(
            False,
            "Нельзя удалить колонку, пока в ней есть задачи.",
            "error",
            workspace_id=workspace_id,
        )

    board.delete_column(column_id, workspace_id=workspace_id)
    return _result(True, "Колонка удалена.", "success", workspace_id=workspace_id)


def create_task(
    board,
    workspace_id: str,
    column_id: str,
    title: str,
    description: str,
    priority: str,
    due_date,
) -> ServiceResult:
    workspace = board.get_workspace(workspace_id)
    if workspace is None:
        return _result(False, "Направление не найдено.", "error", workspace_id=workspace_id)

    column = board.get_column(column_id, workspace_id=workspace_id)
    if column is None:
        return _result(False, "Колонка не найдена.", "error", workspace_id=workspace_id)

    task = board.add_task(
        title=title.strip(),
        description=(description or "").strip(),
        priority=priority,
        due_date=due_date,
        column_id=column_id,
        workspace_id=workspace_id,
    )
    if task is None:
        return _result(False, "Не удалось создать задачу.", "error", workspace_id=workspace_id)

    return _result(True, "Задача добавлена.", "success", workspace_id=workspace_id)


def update_task(
    board,
    workspace_id: str,
    task_id: str,
    title: str,
    description: str,
    priority: str,
    due_date,
    column_id: str,
) -> ServiceResult:
    task = board.get_task(task_id, workspace_id=workspace_id)
    if task is None:
        return _result(False, "Задача не найдена.", "error", workspace_id=workspace_id)

    column = board.get_column(column_id, workspace_id=workspace_id)
    if column is None:
        return _result(False, "Колонка не найдена.", "error", workspace_id=workspace_id)

    board.update_task(
        task_id=task_id,
        title=title.strip(),
        description=(description or "").strip(),
        priority=priority,
        due_date=due_date,
        column_id=column_id,
        workspace_id=workspace_id,
    )
    return _result(True, "Задача обновлена.", "success", workspace_id=workspace_id)


def remove_task(board, workspace_id: str, task_id: str) -> ServiceResult:
    task = board.get_task(task_id, workspace_id=workspace_id)
    if task is None:
        return _result(False, "Задача не найдена.", "error", workspace_id=workspace_id)

    board.delete_task(task_id, workspace_id=workspace_id)
    return _result(True, "Задача удалена.", "success", workspace_id=workspace_id)


def move_task_left(board, workspace_id: str, task_id: str) -> ServiceResult:
    task = board.get_task(task_id, workspace_id=workspace_id)
    if task is None:
        return _result(False, "Задача не найдена.", "error", workspace_id=workspace_id)

    columns = board.list_columns(workspace_id)
    column_ids = [column.id for column in columns]

    if task.column_id not in column_ids:
        return _result(False, "Текущая колонка задачи не найдена.", "error", workspace_id=workspace_id)

    current_index = column_ids.index(task.column_id)
    if current_index == 0:
        return _result(True, "Задача уже в первой колонке.", "info", workspace_id=workspace_id)

    new_column_id = column_ids[current_index - 1]
    board.update_task(
        task_id=task.id,
        title=task.title,
        description=task.description or "",
        priority=task.priority or "medium",
        due_date=task.get_due_date_as_date(),
        column_id=new_column_id,
        workspace_id=workspace_id,
    )
    return _result(True, "Задача перемещена влево.", "success", workspace_id=workspace_id)


def move_task_right(board, workspace_id: str, task_id: str) -> ServiceResult:
    task = board.get_task(task_id, workspace_id=workspace_id)
    if task is None:
        return _result(False, "Задача не найдена.", "error", workspace_id=workspace_id)

    columns = board.list_columns(workspace_id)
    column_ids = [column.id for column in columns]

    if task.column_id not in column_ids:
        return _result(False, "Текущая колонка задачи не найдена.", "error", workspace_id=workspace_id)

    current_index = column_ids.index(task.column_id)
    if current_index >= len(column_ids) - 1:
        return _result(True, "Задача уже в последней колонке.", "info", workspace_id=workspace_id)

    new_column_id = column_ids[current_index + 1]
    board.update_task(
        task_id=task.id,
        title=task.title,
        description=task.description or "",
        priority=task.priority or "medium",
        due_date=task.get_due_date_as_date(),
        column_id=new_column_id,
        workspace_id=workspace_id,
    )
    return _result(True, "Задача перемещена вправо.", "success", workspace_id=workspace_id)


def mark_task_done(board, workspace_id: str, task_id: str) -> ServiceResult:
    task = board.get_task(task_id, workspace_id=workspace_id)
    if task is None:
        return _result(False, "Задача не найдена.", "error", workspace_id=workspace_id)

    done_column = None
    for column in board.list_columns(workspace_id):
        if getattr(column, "is_done_column", False):
            done_column = column
            break

    if done_column is None:
        return _result(False, "Не найдена колонка «Готово».", "error", workspace_id=workspace_id)

    if task.column_id == done_column.id:
        return _result(True, "Задача уже находится в колонке «Готово».", "info", workspace_id=workspace_id)

    board.update_task(
        task_id=task.id,
        title=task.title,
        description=task.description or "",
        priority=task.priority or "medium",
        due_date=task.get_due_date_as_date(),
        column_id=done_column.id,
        workspace_id=workspace_id,
    )
    return _result(True, "Задача перенесена в «Готово».", "success", workspace_id=workspace_id)
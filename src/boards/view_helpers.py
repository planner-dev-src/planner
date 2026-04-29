from typing import Optional

from flask import flash, redirect, request, url_for

from .forms import (
    AddColumnForm,
    AddTaskForm,
    AddWorkspaceForm,
    EditColumnForm,
    EditTaskForm,
    EditWorkspaceForm,
    SimplePostForm,
)


def get_all_workspaces(board):
    return board.list_workspaces()


def get_first_workspace(board):
    workspaces = get_all_workspaces(board)
    return workspaces[0] if workspaces else None


def get_active_workspace(board, workspace_id: Optional[str] = None):
    resolved_workspace_id = (workspace_id or request.args.get("workspace_id") or "").strip()
    if resolved_workspace_id:
        workspace = board.get_workspace(resolved_workspace_id)
        if workspace is not None:
            return workspace
    return get_first_workspace(board)


def redirect_index(workspace_id: Optional[str] = None, **params):
    query = dict(params)

    scroll_y = (request.form.get("_scroll_y") or request.args.get("_scroll_y") or "").strip()
    scroll_x = (request.form.get("_scroll_x") or request.args.get("_scroll_x") or "").strip()

    if scroll_y:
        query["_scroll_y"] = scroll_y
    if scroll_x:
        query["_scroll_x"] = scroll_x

    if workspace_id:
        query["workspace_id"] = workspace_id

    return redirect(url_for("boards.index", **query))


def flash_form_errors(form):
    for field_name, errors in form.errors.items():
        if field_name == "csrf_token":
            continue
        for error in errors:
            flash(error, "error")


def get_prefixed_value(prefix: str, field_name: str, default: str = "") -> str:
    return (request.form.get(f"{prefix}-{field_name}") or default).strip()


def find_submitted_prefix(prefix_start: str, submit_suffix: str = "-submit") -> Optional[str]:
    for key in request.form.keys():
        if key.startswith(prefix_start) and key.endswith(submit_suffix):
            return key[: -len(submit_suffix)]
    return None


def resolve_workspace_id(
    board,
    direct_value: Optional[str] = None,
    prefixed_pairs=None,
    task_id: Optional[str] = None,
    column_id: Optional[str] = None,
) -> Optional[str]:
    if direct_value:
        direct_value = direct_value.strip()
        if direct_value:
            return direct_value

    if prefixed_pairs:
        for prefix, field_name in prefixed_pairs:
            value = get_prefixed_value(prefix, field_name)
            if value:
                return value

    if task_id:
        task = board.get_task(task_id)
        if task is not None:
            task_workspace_id = (getattr(task, "workspace_id", "") or "").strip()
            if task_workspace_id:
                return task_workspace_id

    if column_id:
        for workspace in get_all_workspaces(board):
            column = board.get_column(column_id, workspace_id=workspace.id)
            if column is not None:
                return workspace.id

    first_workspace = get_first_workspace(board)
    return first_workspace.id if first_workspace else None


def get_workspace_or_flash(board, workspace_id: Optional[str]):
    if not workspace_id:
        flash("Не указано направление.", "error")
        return None
    workspace = board.get_workspace(workspace_id)
    if workspace is None:
        flash("Направление не найдено.", "error")
    return workspace


def get_column_or_flash(board, column_id: str, workspace_id: str):
    column = board.get_column(column_id, workspace_id=workspace_id)
    if column is None:
        flash("Колонка не найдена.", "error")
    return column


def get_task_or_flash(board, task_id: str, workspace_id: str):
    task = board.get_task(task_id, workspace_id=workspace_id)
    if task is None:
        flash("Задача не найдена.", "error")
    return task


def get_done_column(board, workspace_id: str):
    for column in board.list_columns(workspace_id):
        if getattr(column, "is_done_column", False):
            return column
    return None


def get_columns_and_tasks(board, workspace_id: str):
    columns = board.list_columns(workspace_id)
    tasks_by_column = {
        column.id: board.get_tasks_by_column(column.id, workspace_id=workspace_id)
        for column in columns
    }
    return columns, tasks_by_column


def can_delete_workspace(board, workspace_id: str) -> bool:
    columns = board.list_columns(workspace_id)
    tasks = board.list_tasks(workspace_id)
    has_tasks = len(tasks) > 0
    has_user_columns = any(not column.is_done_column for column in columns)
    return not has_tasks and not has_user_columns


def get_workspace_delete_block_reason(board, workspace_id: str) -> str:
    columns = board.list_columns(workspace_id)
    tasks = board.list_tasks(workspace_id)

    has_tasks = len(tasks) > 0
    user_columns_count = sum(1 for column in columns if not column.is_done_column)

    if has_tasks and user_columns_count > 0:
        return "Сначала удалите все задачи и пользовательские колонки."
    if has_tasks:
        return "Сначала удалите все задачи в этом направлении."
    if user_columns_count > 0:
        return "Сначала удалите все пользовательские колонки. Системная колонка «Готово» удалится вместе с направлением."
    return ""


def make_edit_task_form(task_id: str, columns):
    form = EditTaskForm(prefix=f"edit-task-{task_id}")
    form.column_id.choices = [(column.id, column.name) for column in columns]
    return form


def build_template_context(
    board,
    workspace_id: Optional[str] = None,
    edit_workspace_id: Optional[str] = None,
    edit_column_id: Optional[str] = None,
    edit_task_id: Optional[str] = None,
):
    workspaces = get_all_workspaces(board)
    active_workspace = get_active_workspace(board, workspace_id=workspace_id)

    add_workspace_form = AddWorkspaceForm(prefix="add-workspace")

    edit_workspace_forms = {}
    delete_workspace_forms = {}
    workspace_delete_state = {}

    for workspace in workspaces:
        edit_form = EditWorkspaceForm(prefix=f"edit-workspace-{workspace.id}")
        edit_form.name.data = workspace.name
        edit_workspace_forms[workspace.id] = edit_form

        delete_form = SimplePostForm(prefix=f"delete-workspace-{workspace.id}")
        delete_form.workspace_id.data = workspace.id
        delete_workspace_forms[workspace.id] = delete_form

        workspace_delete_state[workspace.id] = {
            "can_delete": can_delete_workspace(board, workspace.id),
            "reason": get_workspace_delete_block_reason(board, workspace.id),
        }

    columns = []
    tasks_by_column = {}

    add_column_form = AddColumnForm(prefix="add-column")
    add_task_forms = {}
    edit_column_forms = {}
    delete_column_forms = {}
    edit_task_forms = {}
    delete_task_forms = {}
    move_left_forms = {}
    move_right_forms = {}
    done_forms = {}

    if active_workspace is not None:
        add_column_form.workspace_id.data = active_workspace.id
        columns, tasks_by_column = get_columns_and_tasks(board, active_workspace.id)

        for column in columns:
            add_task_form = AddTaskForm(prefix=f"add-task-{column.id}")
            add_task_form.workspace_id.data = active_workspace.id
            add_task_form.column_id.data = column.id
            add_task_forms[column.id] = add_task_form

            edit_column_form = EditColumnForm(prefix=f"edit-column-{column.id}")
            edit_column_form.workspace_id.data = active_workspace.id
            edit_column_form.name.data = column.name
            edit_column_forms[column.id] = edit_column_form

            delete_column_form = SimplePostForm(prefix=f"delete-column-{column.id}")
            delete_column_form.workspace_id.data = active_workspace.id
            delete_column_forms[column.id] = delete_column_form

        for column in columns:
            for task in tasks_by_column[column.id]:
                edit_task_form = make_edit_task_form(task.id, columns)
                edit_task_form.workspace_id.data = active_workspace.id
                edit_task_form.title.data = task.title
                edit_task_form.description.data = task.description or ""
                edit_task_form.priority.data = task.priority or "medium"
                edit_task_form.due_date.data = task.get_due_date_as_date()
                edit_task_form.column_id.data = task.column_id
                edit_task_forms[task.id] = edit_task_form

                delete_task_form = SimplePostForm(prefix=f"delete-task-{task.id}")
                delete_task_form.workspace_id.data = active_workspace.id
                delete_task_forms[task.id] = delete_task_form

                move_left_form = SimplePostForm(prefix=f"move-left-{task.id}")
                move_left_form.workspace_id.data = active_workspace.id
                move_left_forms[task.id] = move_left_form

                move_right_form = SimplePostForm(prefix=f"move-right-{task.id}")
                move_right_form.workspace_id.data = active_workspace.id
                move_right_forms[task.id] = move_right_form

                done_form = SimplePostForm(prefix=f"done-{task.id}")
                done_form.workspace_id.data = active_workspace.id
                done_forms[task.id] = done_form

    return {
        "workspaces": workspaces,
        "active_workspace": active_workspace,
        "columns": columns,
        "tasks_by_column": tasks_by_column,
        "add_workspace_form": add_workspace_form,
        "edit_workspace_forms": edit_workspace_forms,
        "delete_workspace_forms": delete_workspace_forms,
        "workspace_delete_state": workspace_delete_state,
        "add_column_form": add_column_form,
        "add_task_forms": add_task_forms,
        "edit_column_forms": edit_column_forms,
        "delete_column_forms": delete_column_forms,
        "edit_task_forms": edit_task_forms,
        "delete_task_forms": delete_task_forms,
        "move_left_forms": move_left_forms,
        "move_right_forms": move_right_forms,
        "done_forms": done_forms,
        "edit_workspace_id": edit_workspace_id,
        "edit_column_id": edit_column_id,
        "edit_task_id": edit_task_id,
    }
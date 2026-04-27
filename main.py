from pathlib import Path
from typing import Optional

from flask import Flask, flash, redirect, render_template, request, url_for
from flask_wtf.csrf import CSRFError, CSRFProtect

from forms import (
    AddColumnForm,
    AddTaskForm,
    AddWorkspaceForm,
    EditColumnForm,
    EditTaskForm,
    EditWorkspaceForm,
    SimplePostForm,
)
from src.planner.board import Board


app = Flask(__name__)
app.config["SECRET_KEY"] = "change-this-secret-key-to-a-long-random-value"

csrf = CSRFProtect(app)
board = Board()


def get_all_workspaces():
    return board.list_workspaces()


def get_first_workspace():
    workspaces = get_all_workspaces()
    return workspaces[0] if workspaces else None


def get_active_workspace():
    workspace_id = (request.args.get("workspace_id") or "").strip()
    if workspace_id:
        workspace = board.get_workspace(workspace_id)
        if workspace is not None:
            return workspace
    return get_first_workspace()


def redirect_index(workspace_id: Optional[str] = None, **params):
    query = dict(params)
    if workspace_id:
        query["workspace_id"] = workspace_id
    return redirect(url_for("index", **query))


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
        for workspace in get_all_workspaces():
            column = board.get_column(column_id, workspace_id=workspace.id)
            if column is not None:
                return workspace.id

    first_workspace = get_first_workspace()
    return first_workspace.id if first_workspace else None


def get_workspace_or_flash(workspace_id: Optional[str]):
    if not workspace_id:
        flash("Не указано направление.", "error")
        return None
    workspace = board.get_workspace(workspace_id)
    if workspace is None:
        flash("Направление не найдено.", "error")
    return workspace


def get_column_or_flash(column_id: str, workspace_id: str):
    column = board.get_column(column_id, workspace_id=workspace_id)
    if column is None:
        flash("Колонка не найдена.", "error")
    return column


def get_task_or_flash(task_id: str, workspace_id: str):
    task = board.get_task(task_id, workspace_id=workspace_id)
    if task is None:
        flash("Задача не найдена.", "error")
    return task


def get_done_column(workspace_id: str):
    for column in board.list_columns(workspace_id):
        if getattr(column, "is_done_column", False):
            return column
    return None


def get_columns_and_tasks(workspace_id: str):
    columns = board.list_columns(workspace_id)
    tasks_by_column = {
        column.id: board.get_tasks_by_column(column.id, workspace_id=workspace_id)
        for column in columns
    }
    return columns, tasks_by_column


def can_delete_workspace(workspace_id: str) -> bool:
    columns = board.list_columns(workspace_id)
    tasks = board.list_tasks(workspace_id)
    has_tasks = len(tasks) > 0
    has_user_columns = any(not column.is_done_column for column in columns)
    return not has_tasks and not has_user_columns


def get_workspace_delete_block_reason(workspace_id: str) -> str:
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
    edit_workspace_id: Optional[str] = None,
    edit_column_id: Optional[str] = None,
    edit_task_id: Optional[str] = None,
):
    workspaces = get_all_workspaces()
    active_workspace = get_active_workspace()

    add_workspace_form = AddWorkspaceForm(prefix="add-workspace")

    edit_workspace_forms = {}
    delete_workspace_forms = {}
    workspace_delete_state = {}

    for workspace in workspaces:
        edit_form = EditWorkspaceForm(prefix=f"edit-workspace-{workspace.id}")
        if edit_workspace_id == workspace.id:
            edit_form.name.data = workspace.name
        edit_workspace_forms[workspace.id] = edit_form

        delete_form = SimplePostForm(prefix=f"delete-workspace-{workspace.id}")
        delete_form.workspace_id.data = workspace.id
        delete_workspace_forms[workspace.id] = delete_form

        workspace_delete_state[workspace.id] = {
            "can_delete": can_delete_workspace(workspace.id),
            "reason": get_workspace_delete_block_reason(workspace.id),
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
        columns, tasks_by_column = get_columns_and_tasks(active_workspace.id)

        for column in columns:
            add_task_form = AddTaskForm(prefix=f"add-task-{column.id}")
            add_task_form.workspace_id.data = active_workspace.id
            add_task_form.column_id.data = column.id
            add_task_forms[column.id] = add_task_form

            edit_column_form = EditColumnForm(prefix=f"edit-column-{column.id}")
            edit_column_form.workspace_id.data = active_workspace.id
            if edit_column_id == column.id:
                edit_column_form.name.data = column.name
            edit_column_forms[column.id] = edit_column_form

            delete_column_form = SimplePostForm(prefix=f"delete-column-{column.id}")
            delete_column_form.workspace_id.data = active_workspace.id
            delete_column_forms[column.id] = delete_column_form

        for column in columns:
            for task in tasks_by_column[column.id]:
                edit_task_form = make_edit_task_form(task.id, columns)
                edit_task_form.workspace_id.data = active_workspace.id
                if edit_task_id == task.id:
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


@app.route("/", methods=["GET"])
def index():
    edit_workspace_id = (request.args.get("edit_workspace") or "").strip() or None
    edit_column_id = (request.args.get("edit_column") or "").strip() or None
    edit_task_id = (request.args.get("edit_task") or "").strip() or None

    context = build_template_context(
        edit_workspace_id=edit_workspace_id,
        edit_column_id=edit_column_id,
        edit_task_id=edit_task_id,
    )
    return render_template("index.html", **context)


@app.route("/workspaces/add", methods=["POST"])
def add_workspace():
    form = AddWorkspaceForm(prefix="add-workspace")
    if not form.validate_on_submit():
        flash_form_errors(form)
        return redirect_index()

    workspace = board.add_workspace(form.name.data.strip())
    if workspace is None:
        flash("Не удалось создать направление.", "error")
        return redirect_index()

    flash("Направление создано.", "success")
    return redirect_index(workspace.id)


@app.route("/workspaces/<workspace_id>/edit", methods=["GET", "POST"])
def edit_workspace(workspace_id):
    workspace = get_workspace_or_flash(workspace_id)
    if workspace is None:
        return redirect_index()

    if request.method == "GET":
        return redirect_index(workspace_id, edit_workspace=workspace_id)

    form = EditWorkspaceForm(prefix=f"edit-workspace-{workspace_id}")
    if not form.validate_on_submit():
        flash_form_errors(form)
        return redirect_index(workspace_id, edit_workspace=workspace_id)

    board.update_workspace(workspace_id, form.name.data.strip())
    flash("Направление переименовано.", "success")
    return redirect_index(workspace_id)


@app.route("/workspaces/<workspace_id>/delete", methods=["POST"])
def delete_workspace(workspace_id):
    prefix = f"delete-workspace-{workspace_id}"
    form = SimplePostForm(prefix=prefix)
    fallback_workspace_id = resolve_workspace_id(
        direct_value=request.form.get("workspace_id"),
        prefixed_pairs=[(prefix, "workspace_id")],
    )

    if not form.validate_on_submit():
        flash("Не удалось удалить направление.", "error")
        return redirect_index(fallback_workspace_id)

    workspace = get_workspace_or_flash(workspace_id)
    if workspace is None:
        return redirect_index(fallback_workspace_id)

    if not can_delete_workspace(workspace_id):
        flash(get_workspace_delete_block_reason(workspace_id), "error")
        return redirect_index(workspace_id)

    board.delete_workspace(workspace_id)
    flash("Направление удалено.", "success")
    return redirect_index()


@app.route("/columns/add", methods=["POST"])
def add_column():
    form = AddColumnForm(prefix="add-column")
    workspace_id_raw = resolve_workspace_id(
        direct_value=request.form.get("workspace_id"),
        prefixed_pairs=[("add-column", "workspace_id")],
    )

    if not form.validate_on_submit():
        flash_form_errors(form)
        return redirect_index(workspace_id_raw)

    workspace_id = (form.workspace_id.data or "").strip()
    workspace = get_workspace_or_flash(workspace_id)
    if workspace is None:
        return redirect_index(workspace_id_raw)

    column = board.add_column(form.name.data.strip(), workspace_id=workspace_id)
    if column is None:
        flash("Не удалось создать колонку.", "error")
        return redirect_index(workspace_id)

    flash("Колонка добавлена.", "success")
    return redirect_index(workspace_id)


@app.route("/columns/<column_id>/edit", methods=["GET", "POST"])
def edit_column(column_id):
    prefix = f"edit-column-{column_id}"
    workspace_id = resolve_workspace_id(
        direct_value=request.args.get("workspace_id") or request.form.get("workspace_id"),
        prefixed_pairs=[(prefix, "workspace_id")],
        column_id=column_id,
    )

    if not workspace_id:
        flash("Не указано направление.", "error")
        return redirect_index()

    column = get_column_or_flash(column_id, workspace_id)
    if column is None:
        return redirect_index(workspace_id)

    if request.method == "GET":
        return redirect_index(workspace_id, edit_column=column_id)

    form = EditColumnForm(prefix=prefix)
    if not form.validate_on_submit():
        flash_form_errors(form)
        return redirect_index(workspace_id, edit_column=column_id)

    if getattr(column, "is_done_column", False):
        flash("Системную колонку «Готово» нельзя переименовать.", "error")
        return redirect_index(workspace_id)

    board.update_column(column_id, form.name.data.strip(), workspace_id=workspace_id)
    flash("Колонка переименована.", "success")
    return redirect_index(workspace_id)


@app.route("/columns/<column_id>/delete", methods=["POST"])
def delete_column(column_id):
    prefix = f"delete-column-{column_id}"
    form = SimplePostForm(prefix=prefix)
    workspace_id = resolve_workspace_id(
        direct_value=request.form.get("workspace_id"),
        prefixed_pairs=[(prefix, "workspace_id")],
        column_id=column_id,
    )

    if not form.validate_on_submit():
        flash("Не удалось удалить колонку.", "error")
        return redirect_index(workspace_id)

    if not workspace_id:
        flash("Не указано направление.", "error")
        return redirect_index()

    column = get_column_or_flash(column_id, workspace_id)
    if column is None:
        return redirect_index(workspace_id)

    if getattr(column, "is_done_column", False):
        flash("Системную колонку «Готово» нельзя удалить отдельно.", "error")
        return redirect_index(workspace_id)

    tasks = board.get_tasks_by_column(column_id, workspace_id=workspace_id)
    if tasks:
        flash("Нельзя удалить колонку, пока в ней есть задачи.", "error")
        return redirect_index(workspace_id)

    board.delete_column(column_id, workspace_id=workspace_id)
    flash("Колонка удалена.", "success")
    return redirect_index(workspace_id)


@app.route("/tasks/add", methods=["POST"])
def add_task():
    form_prefix = find_submitted_prefix("add-task-")
    workspace_id_raw = resolve_workspace_id(
        direct_value=request.form.get("workspace_id"),
        prefixed_pairs=[(form_prefix, "workspace_id")] if form_prefix else None,
    )

    if not form_prefix:
        flash("Не удалось определить форму добавления задачи.", "error")
        return redirect_index(workspace_id_raw)

    form = AddTaskForm(prefix=form_prefix)
    if not form.validate_on_submit():
        flash_form_errors(form)
        return redirect_index(workspace_id_raw)

    workspace_id = (form.workspace_id.data or "").strip()
    column_id = (form.column_id.data or "").strip()

    workspace = get_workspace_or_flash(workspace_id)
    if workspace is None:
        return redirect_index(workspace_id_raw)

    column = get_column_or_flash(column_id, workspace_id)
    if column is None:
        return redirect_index(workspace_id)

    task = board.add_task(
        title=form.title.data.strip(),
        description=(form.description.data or "").strip(),
        priority=form.priority.data,
        due_date=form.due_date.data,
        column_id=column_id,
        workspace_id=workspace_id,
    )
    if task is None:
        flash("Не удалось создать задачу.", "error")
        return redirect_index(workspace_id)

    flash("Задача добавлена.", "success")
    return redirect_index(workspace_id)


@app.route("/tasks/<task_id>/edit", methods=["GET", "POST"])
def edit_task(task_id):
    prefix = f"edit-task-{task_id}"
    workspace_id = resolve_workspace_id(
        direct_value=request.args.get("workspace_id") or request.form.get("workspace_id"),
        prefixed_pairs=[(prefix, "workspace_id")],
        task_id=task_id,
    )

    if not workspace_id:
        flash("Не указано направление.", "error")
        return redirect_index()

    task = get_task_or_flash(task_id, workspace_id)
    if task is None:
        return redirect_index(workspace_id)

    columns = board.list_columns(workspace_id)

    if request.method == "GET":
        return redirect_index(workspace_id, edit_task=task_id)

    form = make_edit_task_form(task_id, columns)
    if not form.validate_on_submit():
        flash_form_errors(form)
        return redirect_index(workspace_id, edit_task=task_id)

    new_column = get_column_or_flash(form.column_id.data, workspace_id)
    if new_column is None:
        return redirect_index(workspace_id)

    board.update_task(
        task_id=task_id,
        title=form.title.data.strip(),
        description=(form.description.data or "").strip(),
        priority=form.priority.data,
        due_date=form.due_date.data,
        column_id=form.column_id.data,
        workspace_id=workspace_id,
    )
    flash("Задача обновлена.", "success")
    return redirect_index(workspace_id)


@app.route("/tasks/<task_id>/delete", methods=["POST"])
def delete_task(task_id):
    prefix = f"delete-task-{task_id}"
    form = SimplePostForm(prefix=prefix)
    workspace_id = resolve_workspace_id(
        direct_value=request.form.get("workspace_id"),
        prefixed_pairs=[(prefix, "workspace_id")],
        task_id=task_id,
    )

    if not form.validate_on_submit():
        flash("Не удалось удалить задачу.", "error")
        return redirect_index(workspace_id)

    if not workspace_id:
        flash("Не указано направление.", "error")
        return redirect_index()

    task = get_task_or_flash(task_id, workspace_id)
    if task is None:
        return redirect_index(workspace_id)

    board.delete_task(task_id, workspace_id=workspace_id)
    flash("Задача удалена.", "success")
    return redirect_index(workspace_id)


@app.route("/tasks/<task_id>/move-left", methods=["POST"])
def move_task_left(task_id):
    prefix = f"move-left-{task_id}"
    form = SimplePostForm(prefix=prefix)
    workspace_id = resolve_workspace_id(
        direct_value=request.form.get("workspace_id"),
        prefixed_pairs=[(prefix, "workspace_id")],
        task_id=task_id,
    )

    if not form.validate_on_submit():
        flash("Не удалось переместить задачу.", "error")
        return redirect_index(workspace_id)

    if not workspace_id:
        flash("Не указано направление.", "error")
        return redirect_index()

    task = get_task_or_flash(task_id, workspace_id)
    if task is None:
        return redirect_index(workspace_id)

    columns = board.list_columns(workspace_id)
    column_ids = [column.id for column in columns]

    if task.column_id not in column_ids:
        flash("Текущая колонка задачи не найдена.", "error")
        return redirect_index(workspace_id)

    current_index = column_ids.index(task.column_id)
    if current_index == 0:
        flash("Задача уже в первой колонке.", "info")
        return redirect_index(workspace_id)

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
    flash("Задача перемещена влево.", "success")
    return redirect_index(workspace_id)


@app.route("/tasks/<task_id>/move-right", methods=["POST"])
def move_task_right(task_id):
    prefix = f"move-right-{task_id}"
    form = SimplePostForm(prefix=prefix)
    workspace_id = resolve_workspace_id(
        direct_value=request.form.get("workspace_id"),
        prefixed_pairs=[(prefix, "workspace_id")],
        task_id=task_id,
    )

    if not form.validate_on_submit():
        flash("Не удалось переместить задачу.", "error")
        return redirect_index(workspace_id)

    if not workspace_id:
        flash("Не указано направление.", "error")
        return redirect_index()

    task = get_task_or_flash(task_id, workspace_id)
    if task is None:
        return redirect_index(workspace_id)

    columns = board.list_columns(workspace_id)
    column_ids = [column.id for column in columns]

    if task.column_id not in column_ids:
        flash("Текущая колонка задачи не найдена.", "error")
        return redirect_index(workspace_id)

    current_index = column_ids.index(task.column_id)
    if current_index >= len(column_ids) - 1:
        flash("Задача уже в последней колонке.", "info")
        return redirect_index(workspace_id)

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
    flash("Задача перемещена вправо.", "success")
    return redirect_index(workspace_id)


@app.route("/tasks/<task_id>/done", methods=["POST"])
def mark_task_done(task_id):
    prefix = f"done-{task_id}"
    form = SimplePostForm(prefix=prefix)
    workspace_id = resolve_workspace_id(
        direct_value=request.form.get("workspace_id"),
        prefixed_pairs=[(prefix, "workspace_id")],
        task_id=task_id,
    )

    if not form.validate_on_submit():
        flash("Не удалось завершить задачу.", "error")
        return redirect_index(workspace_id)

    if not workspace_id:
        flash("Не указано направление.", "error")
        return redirect_index()

    task = get_task_or_flash(task_id, workspace_id)
    if task is None:
        return redirect_index(workspace_id)

    done_column = get_done_column(workspace_id)
    if done_column is None:
        flash("Не найдена колонка «Готово».", "error")
        return redirect_index(workspace_id)

    if task.column_id == done_column.id:
        flash("Задача уже находится в колонке «Готово».", "info")
        return redirect_index(workspace_id)

    board.update_task(
        task_id=task.id,
        title=task.title,
        description=task.description or "",
        priority=task.priority or "medium",
        due_date=task.get_due_date_as_date(),
        column_id=done_column.id,
        workspace_id=workspace_id,
    )
    flash("Задача перенесена в «Готово».", "success")
    return redirect_index(workspace_id)


@app.errorhandler(CSRFError)
def handle_csrf_error(error):
    workspace_id = resolve_workspace_id(
        direct_value=request.args.get("workspace_id") or request.form.get("workspace_id")
    )
    flash("Форма устарела или страница была обновлена. Повтори действие.", "error")
    return redirect_index(workspace_id)


if __name__ == "__main__":
    app.run(debug=True)
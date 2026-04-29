from flask import Blueprint, flash, render_template, request
from flask_wtf.csrf import CSRFError

from .forms import (
    AddColumnForm,
    AddTaskForm,
    AddWorkspaceForm,
    EditColumnForm,
    EditWorkspaceForm,
    SimplePostForm,
)
from .services import (
    create_column,
    create_task,
    create_workspace,
    mark_task_done as mark_task_done_service,
    move_task_left as move_task_left_service,
    move_task_right as move_task_right_service,
    remove_column,
    remove_task,
    remove_workspace,
    rename_column,
    rename_workspace,
    update_task,
)
from .view_helpers import (
    build_template_context,
    find_submitted_prefix,
    flash_form_errors,
    make_edit_task_form,
    redirect_index,
    resolve_workspace_id,
)
from src.planner.board import Board


boards_bp = Blueprint(
    "boards",
    __name__,
    url_prefix="/boards",
    template_folder="templates",
)

board = Board()


def _finish(result):
    flash(result.message, result.category)
    params = {}
    if result.edit_workspace_id:
        params["edit_workspace"] = result.edit_workspace_id
    if result.edit_column_id:
        params["edit_column"] = result.edit_column_id
    if result.edit_task_id:
        params["edit_task"] = result.edit_task_id
    return redirect_index(result.workspace_id, **params)


@boards_bp.route("/", methods=["GET"])
def index():
    edit_workspace_id = (request.args.get("edit_workspace") or "").strip() or None
    edit_column_id = (request.args.get("edit_column") or "").strip() or None
    edit_task_id = (request.args.get("edit_task") or "").strip() or None

    context = build_template_context(
        board,
        edit_workspace_id=edit_workspace_id,
        edit_column_id=edit_column_id,
        edit_task_id=edit_task_id,
    )
    return render_template("boards/index.html", **context)


@boards_bp.route("/workspaces/add", methods=["POST"])
def add_workspace():
    form = AddWorkspaceForm(prefix="add-workspace")
    if not form.validate_on_submit():
        flash_form_errors(form)
        return redirect_index()

    result = create_workspace(board, form.name.data)
    return _finish(result)


@boards_bp.route("/workspaces/<workspace_id>/edit", methods=["GET", "POST"])
def edit_workspace(workspace_id):
    if request.method == "GET":
        return redirect_index(workspace_id, edit_workspace=workspace_id)

    form = EditWorkspaceForm(prefix=f"edit-workspace-{workspace_id}")
    if not form.validate_on_submit():
        flash_form_errors(form)
        return redirect_index(workspace_id, edit_workspace=workspace_id)

    result = rename_workspace(board, workspace_id, form.name.data)
    return _finish(result)


@boards_bp.route("/workspaces/<workspace_id>/delete", methods=["POST"])
def delete_workspace(workspace_id):
    prefix = f"delete-workspace-{workspace_id}"
    form = SimplePostForm(prefix=prefix)
    fallback_workspace_id = resolve_workspace_id(
        board,
        direct_value=request.form.get("workspace_id"),
        prefixed_pairs=[(prefix, "workspace_id")],
    )

    if not form.validate_on_submit():
        flash("Не удалось удалить направление.", "error")
        return redirect_index(fallback_workspace_id)

    result = remove_workspace(board, workspace_id)
    return _finish(result)


@boards_bp.route("/columns/add", methods=["POST"])
def add_column():
    form = AddColumnForm(prefix="add-column")
    workspace_id_raw = resolve_workspace_id(
        board,
        direct_value=request.form.get("workspace_id"),
        prefixed_pairs=[("add-column", "workspace_id")],
    )

    if not form.validate_on_submit():
        flash_form_errors(form)
        return redirect_index(workspace_id_raw)

    result = create_column(board, (form.workspace_id.data or "").strip(), form.name.data)
    return _finish(result)


@boards_bp.route("/columns/<column_id>/edit", methods=["GET", "POST"])
def edit_column(column_id):
    prefix = f"edit-column-{column_id}"
    workspace_id = resolve_workspace_id(
        board,
        direct_value=request.args.get("workspace_id") or request.form.get("workspace_id"),
        prefixed_pairs=[(prefix, "workspace_id")],
        column_id=column_id,
    )

    if not workspace_id:
        flash("Не указано направление.", "error")
        return redirect_index()

    if request.method == "GET":
        return redirect_index(workspace_id, edit_column=column_id)

    form = EditColumnForm(prefix=prefix)
    if not form.validate_on_submit():
        flash_form_errors(form)
        return redirect_index(workspace_id, edit_column=column_id)

    result = rename_column(board, workspace_id, column_id, form.name.data)
    return _finish(result)


@boards_bp.route("/columns/<column_id>/delete", methods=["POST"])
def delete_column(column_id):
    prefix = f"delete-column-{column_id}"
    form = SimplePostForm(prefix=prefix)
    workspace_id = resolve_workspace_id(
        board,
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

    result = remove_column(board, workspace_id, column_id)
    return _finish(result)


@boards_bp.route("/tasks/add", methods=["POST"])
def add_task():
    form_prefix = find_submitted_prefix("add-task-")
    workspace_id_raw = resolve_workspace_id(
        board,
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

    result = create_task(
        board=board,
        workspace_id=(form.workspace_id.data or "").strip(),
        column_id=(form.column_id.data or "").strip(),
        title=form.title.data,
        description=form.description.data,
        priority=form.priority.data,
        due_date=form.due_date.data,
    )
    return _finish(result)


@boards_bp.route("/tasks/<task_id>/edit", methods=["GET", "POST"])
def edit_task(task_id):
    prefix = f"edit-task-{task_id}"
    workspace_id = resolve_workspace_id(
        board,
        direct_value=request.args.get("workspace_id") or request.form.get("workspace_id"),
        prefixed_pairs=[(prefix, "workspace_id")],
        task_id=task_id,
    )

    if not workspace_id:
        flash("Не указано направление.", "error")
        return redirect_index()

    if request.method == "GET":
        return redirect_index(workspace_id, edit_task=task_id)

    columns = board.list_columns(workspace_id)
    form = make_edit_task_form(task_id, columns)

    if not form.validate_on_submit():
        flash_form_errors(form)
        return redirect_index(workspace_id, edit_task=task_id)

    result = update_task(
        board=board,
        workspace_id=workspace_id,
        task_id=task_id,
        title=form.title.data,
        description=form.description.data,
        priority=form.priority.data,
        due_date=form.due_date.data,
        column_id=form.column_id.data,
    )
    return _finish(result)


@boards_bp.route("/tasks/<task_id>/delete", methods=["POST"])
def delete_task(task_id):
    prefix = f"delete-task-{task_id}"
    form = SimplePostForm(prefix=prefix)
    workspace_id = resolve_workspace_id(
        board,
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

    result = remove_task(board, workspace_id, task_id)
    return _finish(result)


@boards_bp.route("/tasks/<task_id>/move-left", methods=["POST"])
def move_task_left(task_id):
    prefix = f"move-left-{task_id}"
    form = SimplePostForm(prefix=prefix)
    workspace_id = resolve_workspace_id(
        board,
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

    result = move_task_left_service(board, workspace_id, task_id)
    return _finish(result)


@boards_bp.route("/tasks/<task_id>/move-right", methods=["POST"])
def move_task_right(task_id):
    prefix = f"move-right-{task_id}"
    form = SimplePostForm(prefix=prefix)
    workspace_id = resolve_workspace_id(
        board,
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

    result = move_task_right_service(board, workspace_id, task_id)
    return _finish(result)


@boards_bp.route("/tasks/<task_id>/done", methods=["POST"])
def mark_task_done(task_id):
    prefix = f"done-{task_id}"
    form = SimplePostForm(prefix=prefix)
    workspace_id = resolve_workspace_id(
        board,
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

    result = mark_task_done_service(board, workspace_id, task_id)
    return _finish(result)


@boards_bp.errorhandler(CSRFError)
def handle_csrf_error(error):
    workspace_id = resolve_workspace_id(
        board,
        direct_value=request.args.get("workspace_id") or request.form.get("workspace_id"),
    )
    flash("Форма устарела или страница была обновлена. Повтори действие.", "error")
    return redirect_index(workspace_id)
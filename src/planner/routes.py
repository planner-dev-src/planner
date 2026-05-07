# src/planner/routes.py
from __future__ import annotations

from flask import flash, redirect, render_template, request, url_for

from forms import (
    AddColumnForm,
    AddTaskForm,
    AddWorkspaceForm,
    EditColumnForm,
    EditTaskForm,
    EditWorkspaceForm,
    SimplePostForm,
)
from .services import (
    create_column,
    create_task,
    create_workspace,
    get_column,
    get_task,
    get_workspace,
    list_columns,
    list_tasks_by_column,
    list_workspaces,
    remove_column,
    remove_task,
    remove_workspace,
    rename_column,
    rename_workspace,
    update_task,
)


def build_board_context(current_workspace):
    workspaces = list_workspaces()

    if current_workspace is None and workspaces:
        current_workspace = workspaces[0]

    columns = []
    tasks_by_column = {}

    add_workspace_form = AddWorkspaceForm()
    add_column_form = AddColumnForm()
    add_task_form = AddTaskForm()

    if current_workspace is not None:
        columns = list_columns(current_workspace.id)
        tasks_by_column = {
            column.id: list_tasks_by_column(column.id, workspace_id=current_workspace.id)
            for column in columns
        }
        add_column_form.workspace_id.data = current_workspace.id
        add_task_form.workspace_id.data = current_workspace.id

    selected_column_id = request.args.get("column_id", "").strip()
    if selected_column_id:
        add_task_form.column_id.data = selected_column_id
    elif columns:
        first_non_done = next((column for column in columns if not column.is_done_column), None)
        add_task_form.column_id.data = (
            first_non_done.id if first_non_done is not None else columns[0].id
        )

    return {
        "workspaces": workspaces,
        "current_workspace": current_workspace,
        "columns": columns,
        "tasks_by_column": tasks_by_column,
        "add_workspace_form": add_workspace_form,
        "add_column_form": add_column_form,
        "add_task_form": add_task_form,
        "active_section": "boards",
    }


def board_index():
    workspace_id = request.args.get("workspace_id", "").strip()
    current_workspace = get_workspace(workspace_id) if workspace_id else None

    if current_workspace is None:
        workspaces = list_workspaces()
        if workspaces:
            return redirect(url_for("boards.index", workspace_id=workspaces[0].id))

    context = build_board_context(current_workspace)
    return render_template("boards/index.html", **context)


def create_workspace_view():
    form = AddWorkspaceForm()
    if not form.validate_on_submit():
        for errors in form.errors.values():
            for error in errors:
                flash(error, "error")
        return redirect(url_for("boards.index"))

    workspace = create_workspace(form.name.data)
    if workspace is None:
        flash("Не удалось создать направление.", "error")
        return redirect(url_for("boards.index"))

    flash("Направление создано.", "success")
    return redirect(url_for("boards.index", workspace_id=workspace.id))


def edit_workspace_view(workspace_id: str):
    workspace = get_workspace(workspace_id)
    if workspace is None:
        flash("Направление не найдено.", "error")
        return redirect(url_for("boards.index"))

    form = EditWorkspaceForm()
    if request.method == "GET":
        form.name.data = workspace.name

    if form.validate_on_submit():
        updated = rename_workspace(workspace_id, form.name.data)
        if updated:
            flash("Направление обновлено.", "success")
            return redirect(url_for("boards.index", workspace_id=workspace_id))
        flash("Не удалось обновить направление.", "error")

    return render_template(
        "boards/index.html",
        **build_board_context(workspace),
        edit_workspace_form=form,
        editing_workspace=workspace,
    )


def delete_workspace_view(workspace_id: str):
    form = SimplePostForm()
    if not form.validate_on_submit():
        flash("Некорректный запрос.", "error")
        return redirect(url_for("boards.index", workspace_id=workspace_id))

    deleted = remove_workspace(workspace_id)
    if deleted:
        flash("Направление удалено.", "success")
    else:
        flash("Не удалось удалить направление.", "error")

    remaining = list_workspaces()
    if remaining:
        return redirect(url_for("boards.index", workspace_id=remaining[0].id))
    return redirect(url_for("boards.index"))


def create_column_view():
    form = AddColumnForm()
    if not form.validate_on_submit():
        for errors in form.errors.values():
            for error in errors:
                flash(error, "error")
        return redirect(url_for("boards.index", workspace_id=form.workspace_id.data or None))

    workspace = get_workspace(form.workspace_id.data)
    if workspace is None:
        flash("Направление не найдено.", "error")
        return redirect(url_for("boards.index"))

    column = create_column(
        name=form.name.data,
        workspace_id=workspace.id,
    )
    if column is None:
        flash("Не удалось создать колонку.", "error")
    else:
        flash("Колонка создана.", "success")

    return redirect(url_for("boards.index", workspace_id=workspace.id))


def edit_column_view(column_id: str):
    workspace_id = request.args.get("workspace_id", "").strip()
    column = get_column(column_id, workspace_id=workspace_id or None)
    if column is None:
        flash("Колонка не найдена.", "error")
        return redirect(url_for("boards.index", workspace_id=workspace_id or None))

    workspace = get_workspace(column.workspace_id)
    if workspace is None:
        flash("Направление колонки не найдено.", "error")
        return redirect(url_for("boards.index"))

    form = EditColumnForm()
    if request.method == "GET":
        form.workspace_id.data = workspace.id
        form.name.data = column.name

    if form.validate_on_submit():
        updated = rename_column(
            column_id=column.id,
            name=form.name.data,
            workspace_id=workspace.id,
        )
        if updated:
            flash("Колонка обновлена.", "success")
            return redirect(url_for("boards.index", workspace_id=workspace.id))
        flash("Не удалось обновить колонку.", "error")

    return render_template(
        "boards/index.html",
        **build_board_context(workspace),
        edit_column_form=form,
        editing_column=column,
    )


def delete_column_view(column_id: str):
    form = SimplePostForm()
    workspace_id = form.workspace_id.data or request.args.get("workspace_id", "").strip()

    if not form.validate_on_submit():
        flash("Некорректный запрос.", "error")
        return redirect(url_for("boards.index", workspace_id=workspace_id or None))

    deleted = remove_column(column_id=column_id, workspace_id=workspace_id or None)
    if deleted:
        flash("Колонка удалена.", "success")
    else:
        flash(
            "Не удалось удалить колонку: возможно, она служебная или в ней есть задачи.",
            "error",
        )

    return redirect(url_for("boards.index", workspace_id=workspace_id or None))


def create_task_view():
    form = AddTaskForm()
    if not form.validate_on_submit():
        for errors in form.errors.values():
            for error in errors:
                flash(error, "error")
        return redirect(url_for("boards.index", workspace_id=form.workspace_id.data or None))

    workspace = get_workspace(form.workspace_id.data)
    if workspace is None:
        flash("Направление не найдено.", "error")
        return redirect(url_for("boards.index"))

    task = create_task(
        title=form.title.data,
        description=form.description.data or "",
        priority=form.priority.data,
        due_date=form.due_date.data,
        column_id=form.column_id.data,
        workspace_id=workspace.id,
    )
    if task is None:
        flash("Не удалось создать задачу.", "error")
    else:
        flash("Задача создана.", "success")

    return redirect(url_for("boards.index", workspace_id=workspace.id))


def edit_task_view(task_id: str):
    workspace_id = request.args.get("workspace_id", "").strip()
    task = get_task(task_id, workspace_id=workspace_id or None)
    if task is None:
        flash("Задача не найдена.", "error")
        return redirect(url_for("boards.index", workspace_id=workspace_id or None))

    workspace = get_workspace(task.workspace_id)
    if workspace is None:
        flash("Направление задачи не найдено.", "error")
        return redirect(url_for("boards.index"))

    columns = list_columns(workspace.id)

    form = EditTaskForm()
    form.column_id.choices = [(column.id, column.name) for column in columns]

    if request.method == "GET":
        form.workspace_id.data = workspace.id
        form.title.data = task.title
        form.description.data = task.description
        form.priority.data = task.priority
        form.due_date.data = task.get_due_date_as_date()
        form.column_id.data = task.column_id

    if form.validate_on_submit():
        updated = update_task(
            task_id=task.id,
            title=form.title.data,
            description=form.description.data or "",
            priority=form.priority.data,
            due_date=form.due_date.data,
            column_id=form.column_id.data,
            workspace_id=workspace.id,
        )
        if updated:
            flash("Задача обновлена.", "success")
            return redirect(url_for("boards.index", workspace_id=workspace.id))
        flash("Не удалось обновить задачу.", "error")

    return render_template(
        "boards/index.html",
        **build_board_context(workspace),
        edit_task_form=form,
        editing_task=task,
    )


def delete_task_view(task_id: str):
    form = SimplePostForm()
    workspace_id = form.workspace_id.data or request.args.get("workspace_id", "").strip()

    if not form.validate_on_submit():
        flash("Некорректный запрос.", "error")
        return redirect(url_for("boards.index", workspace_id=workspace_id or None))

    deleted = remove_task(task_id=task_id, workspace_id=workspace_id or None)
    if deleted:
        flash("Задача удалена.", "success")
    else:
        flash("Не удалось удалить задачу.", "error")

    return redirect(url_for("boards.index", workspace_id=workspace_id or None))
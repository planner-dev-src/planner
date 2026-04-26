from flask import Flask, flash, redirect, render_template, request, url_for
from flask_wtf.csrf import CSRFError, CSRFProtect

from forms import (
    AddColumnForm,
    AddTaskForm,
    EditColumnForm,
    EditTaskForm,
    SimplePostForm,
)
from src.planner.board import Board


app = Flask(__name__)
app.config["SECRET_KEY"] = "change-this-secret-key-to-a-long-random-value"

csrf = CSRFProtect(app)
board = Board()


def get_current_workspace():
    return {"name": "Личный планировщик"}


def redirect_index():
    return redirect(url_for("index"))


def flash_form_errors(form):
    for field_name, field_errors in form.errors.items():
        if field_name == "csrf_token":
            continue
        for error in field_errors:
            flash(error, "error")


def get_column_or_flash(column_id):
    column = board.get_column(column_id)
    if column is None:
        flash("Колонка не найдена.", "error")
    return column


def get_task_or_flash(task_id):
    task = board.get_task(task_id)
    if task is None:
        flash("Задача не найдена.", "error")
    return task


def get_done_column():
    for column in board.list_columns():
        if column.is_done_column:
            return column
    return None


def get_columns_and_tasks():
    columns = board.list_columns()
    tasks_by_column = {
        column.id: board.get_tasks_by_column(column.id)
        for column in columns
    }
    return columns, tasks_by_column


def make_edit_task_form(task_id, columns):
    form = EditTaskForm(prefix=f"edit-task-{task_id}")
    form.column_id.choices = [(column.id, column.name) for column in columns]
    return form


def build_template_context(edit_column_id=None, edit_task_id=None):
    columns, tasks_by_column = get_columns_and_tasks()

    add_column_form = AddColumnForm(prefix="add-column")

    add_task_forms = {}
    for column in columns:
        form = AddTaskForm(prefix=f"add-task-{column.id}")
        form.column_id.data = column.id
        add_task_forms[column.id] = form

    edit_column_forms = {}
    for column in columns:
        form = EditColumnForm(prefix=f"edit-column-{column.id}")
        if edit_column_id == column.id:
            form.name.data = column.name
        edit_column_forms[column.id] = form

    edit_task_forms = {}
    for task_list in tasks_by_column.values():
        for task in task_list:
            form = make_edit_task_form(task.id, columns)
            if edit_task_id == task.id:
                form.title.data = task.title
                form.description.data = task.description or ""
                form.priority.data = task.priority or "medium"
                form.due_date.data = task.get_due_date_as_date()
                form.column_id.data = task.column_id
            edit_task_forms[task.id] = form

    delete_column_forms = {
        column.id: SimplePostForm(prefix=f"delete-column-{column.id}")
        for column in columns
    }

    delete_task_forms = {}
    move_left_forms = {}
    move_right_forms = {}
    done_forms = {}

    for task_list in tasks_by_column.values():
        for task in task_list:
            delete_task_forms[task.id] = SimplePostForm(prefix=f"delete-task-{task.id}")
            move_left_forms[task.id] = SimplePostForm(prefix=f"move-left-{task.id}")
            move_right_forms[task.id] = SimplePostForm(prefix=f"move-right-{task.id}")
            done_forms[task.id] = SimplePostForm(prefix=f"done-{task.id}")

    return {
        "columns": columns,
        "tasks_by_column": tasks_by_column,
        "current_workspace": get_current_workspace(),
        "add_column_form": add_column_form,
        "add_task_forms": add_task_forms,
        "edit_column_forms": edit_column_forms,
        "edit_task_forms": edit_task_forms,
        "delete_column_forms": delete_column_forms,
        "delete_task_forms": delete_task_forms,
        "move_left_forms": move_left_forms,
        "move_right_forms": move_right_forms,
        "done_forms": done_forms,
        "edit_column_id": edit_column_id,
        "edit_task_id": edit_task_id,
    }


@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    flash(f"Ошибка безопасности формы: {e.description}", "error")
    return redirect_index()


@app.route("/")
def index():
    return render_template("index.html", **build_template_context())


@app.route("/columns/add", methods=["POST"])
def add_column():
    form = AddColumnForm(prefix="add-column")

    if not form.validate_on_submit():
        flash_form_errors(form)
        return redirect_index()

    column = board.add_column(form.name.data.strip())
    if column is None:
        flash("Не удалось добавить колонку.", "error")
    else:
        flash(f'Колонка "{column.name}" добавлена.', "success")

    return redirect_index()


@app.route("/columns/<column_id>/edit", methods=["GET", "POST"])
def edit_column(column_id):
    column = get_column_or_flash(column_id)
    if column is None:
        return redirect_index()

    if request.method == "GET":
        return render_template(
            "index.html",
            **build_template_context(edit_column_id=column_id),
        )

    form = EditColumnForm(prefix=f"edit-column-{column_id}")

    if not form.validate_on_submit():
        flash_form_errors(form)
        return render_template(
            "index.html",
            **build_template_context(edit_column_id=column_id),
        )

    board.update_column(column_id, form.name.data.strip())
    flash("Колонка обновлена.", "success")
    return redirect_index()


@app.route("/columns/<column_id>/delete", methods=["POST"])
def delete_column(column_id):
    form = SimplePostForm(prefix=f"delete-column-{column_id}")

    if not form.validate_on_submit():
        flash_form_errors(form)
        return redirect_index()

    column = get_column_or_flash(column_id)
    if column is None:
        return redirect_index()

    if column.is_done_column:
        flash('Колонку "Готово" удалять нельзя.', "error")
        return redirect_index()

    if board.get_tasks_by_column(column_id):
        flash("Нельзя удалить колонку, пока в ней есть задачи.", "error")
        return redirect_index()

    board.delete_column(column_id)
    flash(f'Колонка "{column.name}" удалена.', "success")
    return redirect_index()


@app.route("/tasks/add", methods=["POST"])
def add_task():
    columns = board.list_columns()

    matched_column_id = None
    for column in columns:
        submit_name = f"add-task-{column.id}-submit"
        if submit_name in request.form:
            matched_column_id = column.id
            break

    if matched_column_id is None:
        matched_column_id = request.form.get("column_id", "").strip()

    if not matched_column_id:
        flash("Колонка не выбрана.", "error")
        return redirect_index()

    form = AddTaskForm(prefix=f"add-task-{matched_column_id}")

    if not form.validate_on_submit():
        flash_form_errors(form)
        return redirect_index()

    task = board.add_task(
        title=form.title.data.strip(),
        column_id=form.column_id.data,
        description=(form.description.data or "").strip(),
        priority=form.priority.data,
        due_date=form.get_due_date_as_str(),
    )
    if task is None:
        flash("Не удалось добавить задачу.", "error")
    else:
        flash("Задача добавлена.", "success")

    return redirect_index()


@app.route("/tasks/<task_id>/edit", methods=["GET", "POST"])
def edit_task(task_id):
    task = get_task_or_flash(task_id)
    if task is None:
        return redirect_index()

    if request.method == "GET":
        return render_template(
            "index.html",
            **build_template_context(edit_task_id=task_id),
        )

    columns = board.list_columns()
    form = make_edit_task_form(task_id, columns)

    if not form.validate_on_submit():
        flash_form_errors(form)
        return render_template(
            "index.html",
            **build_template_context(edit_task_id=task_id),
        )

    board.update_task(
        task_id=task_id,
        title=form.title.data.strip(),
        column_id=form.column_id.data,
        description=(form.description.data or "").strip(),
        priority=form.priority.data,
        due_date=form.get_due_date_as_str(),
    )
    flash("Задача обновлена.", "success")
    return redirect_index()


@app.route("/tasks/<task_id>/delete", methods=["POST"])
def delete_task(task_id):
    form = SimplePostForm(prefix=f"delete-task-{task_id}")

    if not form.validate_on_submit():
        flash_form_errors(form)
        return redirect_index()

    task = get_task_or_flash(task_id)
    if task is None:
        return redirect_index()

    board.delete_task(task_id)
    flash("Задача удалена.", "success")
    return redirect_index()


@app.route("/tasks/<task_id>/move-left", methods=["POST"])
def move_task_left(task_id):
    form = SimplePostForm(prefix=f"move-left-{task_id}")

    if not form.validate_on_submit():
        flash_form_errors(form)
        return redirect_index()

    task = get_task_or_flash(task_id)
    if task is None:
        return redirect_index()

    columns = board.list_columns()
    column_ids = [column.id for column in columns]

    if task.column_id not in column_ids:
        flash("Текущая колонка задачи не найдена.", "error")
        return redirect_index()

    current_index = column_ids.index(task.column_id)
    if current_index == 0:
        flash("Задача уже в первой колонке.", "info")
        return redirect_index()

    new_column_id = column_ids[current_index - 1]
    board.update_task(
        task.id,
        task.title,
        new_column_id,
        description=task.description,
        priority=task.priority,
        due_date=task.due_date,
    )
    flash("Задача перемещена влево.", "success")
    return redirect_index()


@app.route("/tasks/<task_id>/move-right", methods=["POST"])
def move_task_right(task_id):
    form = SimplePostForm(prefix=f"move-right-{task_id}")

    if not form.validate_on_submit():
        flash_form_errors(form)
        return redirect_index()

    task = get_task_or_flash(task_id)
    if task is None:
        return redirect_index()

    columns = board.list_columns()
    column_ids = [column.id for column in columns]

    if task.column_id not in column_ids:
        flash("Текущая колонка задачи не найдена.", "error")
        return redirect_index()

    current_index = column_ids.index(task.column_id)
    if current_index >= len(column_ids) - 1:
        flash("Задача уже в последней колонке.", "info")
        return redirect_index()

    new_column_id = column_ids[current_index + 1]
    board.update_task(
        task.id,
        task.title,
        new_column_id,
        description=task.description,
        priority=task.priority,
        due_date=task.due_date,
    )
    flash("Задача перемещена вправо.", "success")
    return redirect_index()


@app.route("/tasks/<task_id>/done", methods=["POST"])
def mark_task_done(task_id):
    form = SimplePostForm(prefix=f"done-{task_id}")

    if not form.validate_on_submit():
        flash_form_errors(form)
        return redirect_index()

    task = get_task_or_flash(task_id)
    if task is None:
        return redirect_index()

    done_column = get_done_column()
    if done_column is None:
        flash('Колонка "Готово" не найдена.', "error")
        return redirect_index()

    if task.column_id == done_column.id:
        flash("Задача уже находится в колонке Готово.", "info")
        return redirect_index()

    board.update_task(
        task.id,
        task.title,
        done_column.id,
        description=task.description,
        priority=task.priority,
        due_date=task.due_date,
    )
    flash("Задача отмечена как выполненная.", "success")
    return redirect_index()


if __name__ == "__main__":
    app.run(debug=True)
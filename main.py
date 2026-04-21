from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from flask import Flask, render_template, request, redirect, url_for, abort
from planner.board import Board

app = Flask(__name__)
board = Board(storage_path=PROJECT_ROOT / "board.json")


@app.route("/", methods=["GET"])
def index():
    columns = board.list_columns()
    tasks_by_column = {
        column.id: board.get_tasks_by_column(column.id)
        for column in columns
    }
    return render_template(
        "index.html",
        columns=columns,
        tasks_by_column=tasks_by_column,
    )


@app.route("/columns/add", methods=["POST"])
def add_column():
    name = request.form.get("name", "").strip()
    if name:
        board.add_column(name)
    return redirect(url_for("index"))


@app.route("/columns/<column_id>/edit", methods=["GET", "POST"])
def edit_column(column_id: str):
    column = board.get_column(column_id)
    if column is None:
        abort(404)

    if request.method == "POST":
        new_name = request.form.get("name", "").strip()
        if new_name:
            board.update_column(column_id, new_name)
            return redirect(url_for("index"))

    return render_template("edit_column.html", column=column)


@app.route("/columns/<column_id>/delete", methods=["POST"])
def delete_column(column_id: str):
    board.delete_column(column_id)
    return redirect(url_for("index"))


@app.route("/tasks/add", methods=["POST"])
def add_task():
    title = request.form.get("title", "").strip()
    column_id = request.form.get("column_id", "").strip()

    if title and column_id:
        board.add_task(title, column_id)

    return redirect(url_for("index"))


@app.route("/tasks/<task_id>/edit", methods=["GET", "POST"])
def edit_task(task_id: str):
    task = board.get_task(task_id)
    if task is None:
        abort(404)

    columns = board.list_columns()

    if request.method == "POST":
        new_title = request.form.get("title", "").strip()
        new_column_id = request.form.get("column_id", "").strip()

        if new_title and new_column_id:
            board.update_task(task_id, new_title, new_column_id)
            return redirect(url_for("index"))

    return render_template(
        "edit_task.html",
        task=task,
        columns=columns,
    )


@app.route("/tasks/<task_id>/delete", methods=["POST"])
def delete_task(task_id: str):
    board.delete_task(task_id)
    return redirect(url_for("index"))


@app.route("/tasks/<task_id>/move-left", methods=["POST"])
def move_task_left(task_id: str):
    board.move_task_left(task_id)
    return redirect(url_for("index"))


@app.route("/tasks/<task_id>/move-right", methods=["POST"])
def move_task_right(task_id: str):
    board.move_task_right(task_id)
    return redirect(url_for("index"))


@app.route("/tasks/<task_id>/done", methods=["POST"])
def mark_task_done(task_id: str):
    board.move_task_to_done(task_id)
    return redirect(url_for("index"))


def main() -> None:
    app.run(debug=True, use_reloader=False, port=5000)


if __name__ == "__main__":
    main()
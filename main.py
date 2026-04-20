from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from flask import Flask, render_template, request, redirect, url_for, abort
from planner.board import Board

app = Flask(__name__)
board = Board(storage_path=PROJECT_ROOT / "tasks.json")


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if title:
            board.add_task(title)
        return redirect(url_for("index"))

    current_filter = request.args.get("filter", "all").strip().lower()
    all_tasks = board.list_tasks()

    if current_filter == "active":
        tasks = [task for task in all_tasks if not task.done]
    elif current_filter == "done":
        tasks = [task for task in all_tasks if task.done]
    else:
        current_filter = "all"
        tasks = all_tasks

    return render_template(
        "index.html",
        tasks=tasks,
        current_filter=current_filter,
    )


@app.route("/tasks/<task_id>/done", methods=["POST"])
def mark_done(task_id: str):
    board.mark_task_done(task_id)
    current_filter = request.args.get("filter", "all")
    return redirect(url_for("index", filter=current_filter))


@app.route("/tasks/<task_id>/delete", methods=["POST"])
def delete_task(task_id: str):
    board.delete_task(task_id)
    current_filter = request.args.get("filter", "all")
    return redirect(url_for("index", filter=current_filter))


@app.route("/tasks/<task_id>/edit", methods=["GET", "POST"])
def edit_task(task_id: str):
    task = board.get_task(task_id)
    if task is None:
        abort(404)

    current_filter = request.args.get("filter", "all")

    if request.method == "POST":
        new_title = request.form.get("title", "").strip()
        if new_title:
            board.update_task(task_id, new_title)
            return redirect(url_for("index", filter=current_filter))

    return render_template(
        "edit_task.html",
        task=task,
        current_filter=current_filter,
    )


def main() -> None:
    app.run(debug=True, use_reloader=False, port=5000)


if __name__ == "__main__":
    main()
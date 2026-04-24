from __future__ import annotations

from flask import Flask, redirect, render_template, request, url_for

from src.planner.board import Board

app = Flask(__name__)
board = Board()


@app.get("/")
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


@app.post("/columns/add")
def add_column():
    name = request.form.get("name", "")
    board.add_column(name)
    return redirect(url_for("index"))


@app.route("/columns/<column_id>/edit", methods=["GET", "POST"])
def edit_column(column_id: str):
    column = board.get_column(column_id)
    if column is None:
        return redirect(url_for("index"))

    if request.method == "POST":
        name = request.form.get("name", "")
        board.update_column(column_id, name)
        return redirect(url_for("index"))

    return f"""
    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <title>Rename column</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 520px;
                margin: 40px auto;
                padding: 0 16px;
                color: #222;
                background: #f5f7fb;
            }}
            .card {{
                background: white;
                border: 1px solid #ddd;
                border-radius: 10px;
                padding: 20px;
            }}
            input[type="text"] {{
                width: 100%;
                box-sizing: border-box;
                padding: 10px 12px;
                border: 1px solid #ccc;
                border-radius: 6px;
                margin: 12px 0 16px;
                font-size: 14px;
            }}
            .actions {{
                display: flex;
                gap: 8px;
            }}
            .btn {{
                display: inline-block;
                border: none;
                border-radius: 6px;
                padding: 8px 12px;
                color: white;
                cursor: pointer;
                font-size: 14px;
                text-decoration: none;
            }}
            .btn-primary {{ background-color: #2563eb; }}
            .btn-secondary {{ background-color: #6b7280; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>Rename column</h1>
            <form method="post">
                <input type="text" name="name" value="{column.name}" required>
                <div class="actions">
                    <button type="submit" class="btn btn-primary">Save</button>
                    <a href="{url_for('index')}" class="btn btn-secondary">Cancel</a>
                </div>
            </form>
        </div>
    </body>
    </html>
    """


@app.post("/columns/<column_id>/delete")
def delete_column(column_id: str):
    board.delete_column(column_id)
    return redirect(url_for("index"))


@app.post("/tasks/add")
def add_task():
    title = request.form.get("title", "")
    column_id = request.form.get("column_id", "")
    board.add_task(title, column_id)
    return redirect(url_for("index"))


@app.route("/tasks/<task_id>/edit", methods=["GET", "POST"])
def edit_task(task_id: str):
    task = board.get_task(task_id)
    if task is None:
        return redirect(url_for("index"))

    columns = board.list_columns()

    if request.method == "POST":
        title = request.form.get("title", "")
        column_id = request.form.get("column_id", "")
        board.update_task(task_id, title, column_id)
        return redirect(url_for("index"))

    options_html = []
    for column in columns:
        selected = "selected" if column.id == task.column_id else ""
        options_html.append(
            f'<option value="{column.id}" {selected}>{column.name}</option>'
        )

    return f"""
    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <title>Edit task</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 520px;
                margin: 40px auto;
                padding: 0 16px;
                color: #222;
                background: #f5f7fb;
            }}
            .card {{
                background: white;
                border: 1px solid #ddd;
                border-radius: 10px;
                padding: 20px;
            }}
            input[type="text"], select {{
                width: 100%;
                box-sizing: border-box;
                padding: 10px 12px;
                border: 1px solid #ccc;
                border-radius: 6px;
                margin: 12px 0 16px;
                font-size: 14px;
                background: white;
            }}
            .actions {{
                display: flex;
                gap: 8px;
            }}
            .btn {{
                display: inline-block;
                border: none;
                border-radius: 6px;
                padding: 8px 12px;
                color: white;
                cursor: pointer;
                font-size: 14px;
                text-decoration: none;
            }}
            .btn-primary {{ background-color: #2563eb; }}
            .btn-secondary {{ background-color: #6b7280; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>Edit task</h1>
            <form method="post">
                <input type="text" name="title" value="{task.title}" required>
                <select name="column_id" required>
                    {''.join(options_html)}
                </select>
                <div class="actions">
                    <button type="submit" class="btn btn-primary">Save</button>
                    <a href="{url_for('index')}" class="btn btn-secondary">Cancel</a>
                </div>
            </form>
        </div>
    </body>
    </html>
    """


@app.post("/tasks/<task_id>/delete")
def delete_task(task_id: str):
    board.delete_task(task_id)
    return redirect(url_for("index"))


@app.post("/tasks/<task_id>/move-left")
def move_task_left(task_id: str):
    board.move_task_left(task_id)
    return redirect(url_for("index"))


@app.post("/tasks/<task_id>/move-right")
def move_task_right(task_id: str):
    board.move_task_right(task_id)
    return redirect(url_for("index"))


@app.post("/tasks/<task_id>/done")
def mark_task_done(task_id: str):
    board.move_task_to_done(task_id)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
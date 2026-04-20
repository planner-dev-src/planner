from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from flask import Flask, render_template, request, redirect, url_for

from planner.board import Board

app = Flask(__name__)
board = Board()


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if title:
            board.add_task(title)
        return redirect(url_for("index"))

    return render_template("index.html", tasks=board.list_tasks())


@app.route("/tasks/<task_id>/done", methods=["POST"])
def mark_done(task_id: str):
    board.mark_task_done(task_id)
    return redirect(url_for("index"))


def main() -> None:
    app.run(debug=True, port=5000)


if __name__ == "__main__":
    main()
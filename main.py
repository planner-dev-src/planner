from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from flask import Flask, render_template, request, redirect, url_for

from planner.board import Board

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.jinja_env.auto_reload = True

board = Board()


def seed_demo_data() -> None:
    first_task = board.add_task("Create Task dataclass")
    board.add_task("Create Board class")
    board.add_task("Open planner in browser")
    board.mark_task_done(first_task.id)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if title:
            board.add_task(title)
        return redirect(url_for("index"))

    return render_template("index.html", tasks=board.list_tasks())


def main() -> None:
    seed_demo_data()
    app.run(debug=True, port=5000)


if __name__ == "__main__":
    main()
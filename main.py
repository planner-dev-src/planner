from flask import Flask, render_template

from planner.board import Board

app = Flask(__name__)
board = Board()


def seed_demo_data() -> None:
    first_task = board.add_task("Create Task dataclass")
    board.add_task("Create Board class")
    board.add_task("Open planner in browser")
    board.mark_task_done(first_task.id)


@app.route("/")
def index():
    return render_template("index.html", tasks=board.list_tasks())


def main() -> None:
    seed_demo_data()
    app.run(debug=False, port=5000)


if __name__ == "__main__":
    main()

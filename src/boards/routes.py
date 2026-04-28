from flask import Blueprint, render_template

boards_bp = Blueprint("boards", __name__, url_prefix="/boards")


@boards_bp.route("/")
def index():
    workspaces = [{"id": "default", "name": "Default Workspace"}]
    current_workspace = workspaces[0]

    columns = [
        {"id": "todo", "name": "To Do"},
        {"id": "doing", "name": "Doing"},
        {"id": "done", "name": "Done"},
    ]

    tasks_by_column = {
        "todo": [{"title": "Перенести текущий board в новый модуль"}],
        "doing": [{"title": "Собрать shell + Blueprints"}],
        "done": [{"title": "Создать новую ветку"}],
    }

    return render_template(
        "boards/board.html",
        workspaces=workspaces,
        current_workspace=current_workspace,
        columns=columns,
        tasks_by_column=tasks_by_column,
        active_section="boards",
    )
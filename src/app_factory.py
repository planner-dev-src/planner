from pathlib import Path

from flask import Flask

from src.ui.shell import ui_bp
from src.boards.routes import boards_bp


def create_app():
    project_root = Path(__file__).resolve().parent.parent

    app = Flask(
        __name__,
        template_folder=str(project_root / "templates"),
        static_folder=str(project_root / "static"),
    )

    app.config["SECRET_KEY"] = "dev-secret-key"

    app.register_blueprint(ui_bp)
    app.register_blueprint(boards_bp)

    return app
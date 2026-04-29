from pathlib import Path

from flask import Flask
from flask_wtf.csrf import CSRFProtect

from src.boards.routes import boards_bp
from src.ui.shell import ui_bp

csrf = CSRFProtect()


def create_app():
    project_root = Path(__file__).resolve().parent.parent

    app = Flask(
        __name__,
        template_folder=str(project_root / "templates"),
        static_folder=str(project_root / "static"),
    )

    app.config["SECRET_KEY"] = "change-this-secret-key-to-a-long-random-value"

    csrf.init_app(app)

    app.register_blueprint(ui_bp)
    app.register_blueprint(boards_bp)

    return app
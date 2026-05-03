from pathlib import Path

from flask import Flask
from flask_wtf.csrf import CSRFProtect

from src.boards import boards_bp
from src.knowledge import init_app as init_knowledge
from src.projects import projects_bp
from src.ui import ui_bp


csrf = CSRFProtect()


def create_app():
    app = Flask(
        __name__,
        template_folder=str(Path(__file__).resolve().parents[1] / "templates"),
        static_folder=str(Path(__file__).resolve().parents[1] / "static"),
    )

    app.config["SECRET_KEY"] = "dev-secret-key"
    app.config["WTF_CSRF_ENABLED"] = True

    csrf.init_app(app)

    app.register_blueprint(ui_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(boards_bp)

    init_knowledge(app)

    return app
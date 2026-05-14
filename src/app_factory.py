from pathlib import Path

from flask import Flask
from flask_wtf.csrf import CSRFProtect

from src.config import Config
from src.extensions import db

from src.boards import boards_bp
from src.goals import goals_bp
from src.knowledge import init_app as init_knowledge
from src.materials import materials_bp
from src.monitoring import monitoring_bp
from src.programs import bp as programs_bp
from src.projects import projects_bp
from src.ui import ui_bp
from src.workspaces import workspaces_bp

from src.db_init import init_db

# импорт моделей, чтобы db.create_all() увидел таблицы
from src.workspaces.models import Workspace  # noqa: F401


csrf = CSRFProtect()


def create_app():
    base_dir = Path(__file__).resolve().parents[1]

    app = Flask(
        __name__,
        template_folder=str(base_dir / "templates"),
        static_folder=str(base_dir / "static"),
    )

    app.config.from_object(Config)

    csrf.init_app(app)
    db.init_app(app)

    app.register_blueprint(ui_bp)
    app.register_blueprint(workspaces_bp)
    app.register_blueprint(goals_bp)
    app.register_blueprint(programs_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(boards_bp)
    app.register_blueprint(monitoring_bp)
    app.register_blueprint(materials_bp)

    init_knowledge(app)

    init_db(app)

    @app.context_processor
    def inject_layout_context():
        blueprints = app.blueprints
        return {
            "registered_blueprints": blueprints,
            "has_workspaces_bp": "workspaces" in blueprints,
            "has_goals_bp": "goals" in blueprints,
            "has_programs_bp": "programs" in blueprints,
            "has_projects_bp": "projects" in blueprints,
            "has_boards_bp": "boards" in blueprints,
            "has_monitoring_bp": "monitoring" in blueprints,
            "has_materials_bp": "materials" in blueprints,
            "has_tools_bp": "tools" in blueprints,
        }

    return app
from pathlib import Path

from flask import Flask
from flask_wtf.csrf import CSRFProtect

from src.boards import boards_bp
from src.goals import goals_bp
from src.knowledge import init_app as init_knowledge
from src.materials import materials_bp
from src.monitoring import monitoring_bp
from src.programs import bp as programs_bp
from src.projects import projects_bp
from src.ui import ui_bp
from src.db import close_db
from src.db_migrations import run_migrations

csrf = CSRFProtect()


def create_app():
    base_dir = Path(__file__).resolve().parents[1]

    app = Flask(
        __name__,
        template_folder=str(base_dir / "templates"),
        static_folder=str(base_dir / "static"),
    )

    app.config["SECRET_KEY"] = "dev-secret-key"
    app.config["WTF_CSRF_ENABLED"] = True
    app.config.setdefault("DATABASE", str(base_dir / "planner.db"))

    csrf.init_app(app)
    app.teardown_appcontext(close_db)

    app.register_blueprint(ui_bp)

    app.register_blueprint(goals_bp)
    app.register_blueprint(programs_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(boards_bp)
    app.register_blueprint(monitoring_bp)
    app.register_blueprint(materials_bp)

    init_knowledge(app)

    with app.app_context():
        run_migrations()

    @app.context_processor
    def inject_layout_context():
        blueprints = app.blueprints
        return {
            "registered_blueprints": blueprints,
            "has_programs_bp": "programs" in blueprints,
            "has_projects_bp": "projects" in blueprints,
            "has_monitoring_bp": "monitoring" in blueprints,
            "has_materials_bp": "materials" in blueprints,
            "has_tools_bp": "tools" in blueprints,
        }

    return app
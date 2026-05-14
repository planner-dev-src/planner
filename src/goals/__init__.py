from flask import Blueprint

goals_bp = Blueprint(
    "goals",
    __name__,
    url_prefix="/goals",
    template_folder="templates",
)

from . import routes  # noqa: E402

def init_app(app):
    """Опциональный helper, если хочется инициализировать по модульной схеме."""
    app.register_blueprint(goals_bp)
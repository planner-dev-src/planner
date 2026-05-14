from flask import Blueprint

monitoring_bp = Blueprint(
    "monitoring",
    __name__,
    url_prefix="/monitoring",
)
from . import routes  # noqa: E402,F401
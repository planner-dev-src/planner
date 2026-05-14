from flask import Blueprint

materials_bp = Blueprint(
    "materials",
    __name__,
    url_prefix="/materials",
)
from . import routes  # noqa: E402,F401
from flask import Blueprint

bp = Blueprint(
    "programs",
    __name__,
    url_prefix="/programs",
)

from . import routes  # noqa: E402,F401
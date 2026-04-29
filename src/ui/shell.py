from flask import Blueprint, redirect, url_for

ui_bp = Blueprint("ui", __name__)


@ui_bp.route("/")
def root():
    return redirect(url_for("boards.index"))
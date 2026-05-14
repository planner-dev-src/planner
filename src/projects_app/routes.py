from flask import render_template
from . import bp


@bp.route('/projects/')
def index():
    projects = []  # потом подставишь реальный репозиторий
    return render_template(
        'projects/index.html',
        projects=projects,
        active_section='projects',
    )
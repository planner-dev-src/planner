from flask import render_template
from . import bp


@bp.route('/tools/')
def index():
    # здесь будут специальные инструменты для пользователей
    return render_template(
        'tools/index.html',
        active_section='tools',
    )
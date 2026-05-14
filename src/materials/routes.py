from flask import render_template

from . import materials_bp


@materials_bp.get("/")
def index():
    return render_template(
        "stubs/section_stub.html",
        page_title="Materials (stub)",
        page_heading="Materials (stub)",
        page_description="Здесь позже будет каталог материалов для текущего workspace.",
        active_section="materials",
    )
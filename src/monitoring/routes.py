from flask import render_template

from . import monitoring_bp


@monitoring_bp.get("/")
def index():
    return render_template(
        "stubs/section_stub.html",
        page_title="Monitoring (stub)",
        page_heading="Monitoring (stub)",
        page_description="Здесь позже будет мониторинг по текущему workspace.",
        active_section="monitoring",
    )
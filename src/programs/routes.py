import mimetypes
import os
from dataclasses import dataclass

from flask import (
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)

from . import bp
from .attachments_repository import ProgramAttachmentRepository
from .models import new_program
from .repository import ProgramRepository
from src.projects.forms import ProjectForm
from src.projects.repository import ProjectRepository


def current_user_id() -> str:
    return "local-dev-user"


@dataclass
class ProgramMonitoring:
    total_projects: int
    in_progress: int
    completed: int
    planned: int
    on_hold: int


def build_program_monitoring(projects) -> ProgramMonitoring:
    total = len(projects)
    in_progress = sum(1 for p in projects if getattr(p, "status", None) == "in_progress")
    completed = sum(1 for p in projects if getattr(p, "status", None) == "completed")
    planned = sum(1 for p in projects if getattr(p, "status", None) == "planned")
    on_hold = sum(1 for p in projects if getattr(p, "status", None) == "on_hold")
    return ProgramMonitoring(
        total_projects=total,
        in_progress=in_progress,
        completed=completed,
        planned=planned,
        on_hold=on_hold,
    )


def _load_program_or_404(program_id: str):
    user_id = current_user_id()
    program = ProgramRepository.get_by_id_for_user(program_id, user_id)
    if program is None:
        abort(404)
    return user_id, program


def _render_program_index(
    *,
    show_archived: bool,
    create_error=None,
    create_open=False,
    create_title_value="",
    create_note_value="",
):
    user_id = current_user_id()
    programs = (
        ProgramRepository.list_archived_for_user(user_id)
        if show_archived
        else ProgramRepository.list_active_for_user(user_id)
    )

    return render_template(
        "programs/index.html",
        programs=programs,
        show_archived=show_archived,
        active_section="programs",
        create_error=create_error,
        create_open=create_open,
        create_title_value=create_title_value,
        create_note_value=create_note_value,
    )


def _render_program_detail(
    program,
    *,
    edit_error=None,
    edit_open=False,
    edit_title_value=None,
    edit_note_value=None,
):
    projects = ProjectRepository.list_for_program(program.id)
    attachments = ProgramAttachmentRepository.list_for_program(program.id)
    monitoring = build_program_monitoring(projects)

    return render_template(
        "programs/detail.html",
        program=program,
        projects=projects,
        attachments=attachments,
        monitoring=monitoring,
        active_section="programs",
        edit_error=edit_error,
        edit_open=edit_open,
        edit_title_value=program.title if edit_title_value is None else edit_title_value,
        edit_note_value=(program.note_raw or "") if edit_note_value is None else edit_note_value,
        project_form=ProjectForm(),
    )


@bp.route("/", methods=["GET"])
def index():
    return _render_program_index(show_archived=False)


@bp.route("/archived/", methods=["GET"])
def archived():
    return _render_program_index(show_archived=True)


@bp.route("/create/", methods=["GET", "POST"])
def create():
    if request.method == "GET":
        return _render_program_index(show_archived=False, create_open=True)

    title = (request.form.get("title") or "").strip()
    note = (request.form.get("note") or "").strip()

    if not title:
        flash("Название программы обязательно.", "error")
        return _render_program_index(
            show_archived=False,
            create_error="Название программы обязательно.",
            create_open=True,
            create_title_value=title,
            create_note_value=note,
        )

    program = new_program(
        title=title,
        owner_id=current_user_id(),
        note_html=note,
        note_raw=note,
    )
    ProgramRepository.save(program)

    flash("Программа создана.", "success")
    return redirect(url_for("programs.detail", program_id=program.id))


@bp.route("/<program_id>/", methods=["GET"])
def detail(program_id):
    _, program = _load_program_or_404(program_id)
    return _render_program_detail(program)


@bp.route("/<program_id>/edit/", methods=["POST"])
def edit(program_id):
    user_id, program = _load_program_or_404(program_id)

    title = (request.form.get("title") or "").strip()
    note = (request.form.get("note") or "").strip()

    if not title:
        flash("Не удалось обновить программу: укажи название.", "error")
        return _render_program_detail(
            program,
            edit_error="Название программы обязательно.",
            edit_open=True,
            edit_title_value=title,
            edit_note_value=note,
        )

    updated = ProgramRepository.update(
        program_id=program_id,
        owner_id=user_id,
        title=title,
        note_raw=note,
        note_html=note,
    )

    if not updated:
        abort(404)

    flash("Программа обновлена.", "success")
    return redirect(url_for("programs.detail", program_id=program_id))


@bp.route("/<program_id>/archive/", methods=["POST"])
def archive(program_id):
    user_id, _program = _load_program_or_404(program_id)

    archived_ok = ProgramRepository.archive(program_id, user_id)
    if not archived_ok:
        abort(404)

    flash("Программа отправлена в архив.", "success")
    return redirect(url_for("programs.index"))


@bp.route("/<program_id>/unarchive/", methods=["POST"])
def unarchive(program_id):
    user_id, _program = _load_program_or_404(program_id)

    unarchived_ok = ProgramRepository.unarchive(program_id, user_id)
    if not unarchived_ok:
        abort(404)

    flash("Программа восстановлена из архива.", "success")
    return redirect(url_for("programs.archived"))


@bp.route("/<program_id>/attachments/upload", methods=["POST"])
def upload_attachment(program_id):
    user_id, _program = _load_program_or_404(program_id)

    file = request.files.get("file")
    if not file or file.filename == "":
        flash("Файл не выбран.", "error")
        return redirect(url_for("programs.detail", program_id=program_id))

    kind = (request.form.get("kind") or "appendix").strip() or "appendix"

    uploads_dir = current_app.config.get("UPLOADS_DIR", "uploads")
    os.makedirs(uploads_dir, exist_ok=True)

    stored_name = f"{program_id}_{file.filename}"
    stored_path = os.path.join(uploads_dir, stored_name)
    file.save(stored_path)

    content_type, _ = mimetypes.guess_type(file.filename)
    ProgramAttachmentRepository.add(
        program_id=program_id,
        kind=kind,
        filename=file.filename,
        stored_path=stored_path,
        content_type=content_type,
        uploaded_by=user_id,
    )

    flash("Файл загружен.", "success")
    return redirect(url_for("programs.detail", program_id=program_id))


@bp.route("/attachments/<attachment_id>/download", methods=["GET"])
def download_attachment(attachment_id):
    att = ProgramAttachmentRepository.get(attachment_id)
    if att is None:
        abort(404)

    return send_file(
        att.stored_path,
        mimetype=att.content_type or "application/octet-stream",
        as_attachment=True,
        download_name=att.filename,
    )
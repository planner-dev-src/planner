from __future__ import annotations

from flask import abort, flash, redirect, render_template, request, url_for

from . import projects_bp
from .forms import (
    AttachExistingProjectForm,
    CloneProjectTreeForm,
    DeleteProjectForm,
    MoveProjectForm,
    ProjectForm,
)
from .services import (
    archive_project,
    attach_existing_project,
    build_project_tree,
    can_delete_project,
    clone_project_tree,
    create_project,
    delete_project_with_policy,
    get_project,
    list_archived_root_projects,
    list_child_projects,
    list_possible_parents,
    list_projects_for_clone_choice,
    list_root_projects,
    move_project,
    restore_project,
    update_project,
)


@projects_bp.get("/")
def projects_list():
    projects = list_root_projects()
    return render_template(
        "projects/list.html",
        projects=projects,
        active_section="projects",
    )


@projects_bp.get("/archive")
def projects_archive():
    projects = list_archived_root_projects()
    return render_template(
        "projects/archive.html",
        projects=projects,
        active_section="projects",
    )


@projects_bp.route("/create", methods=["GET", "POST"])
def project_create():
    form = ProjectForm()

    if form.validate_on_submit():
        try:
            project = create_project(
                title=form.title.data,
                description=form.description.data or "",
                parent_id=None,
                program_id=None,
            )
        except ValueError as exc:
            flash(str(exc), "error")
        else:
            flash("Проект создан.", "success")
            return redirect(
                url_for("projects.project_detail", project_id=project.id)
            )

    return render_template(
        "projects/create.html",
        form=form,
        parent_project=None,
        active_section="projects",
    )


@projects_bp.post("/programs/<program_id>/create")
def project_create_for_program(program_id: str):
    form = ProjectForm()

    if not form.validate_on_submit():
        flash("Не удалось создать проект. Проверьте заполнение формы.", "error")
        return redirect(url_for("programs.detail", program_id=program_id))

    try:
        project = create_project(
            title=form.title.data,
            description=form.description.data or "",
            parent_id=None,
            program_id=program_id,
        )
    except ValueError as exc:
        flash(str(exc), "error")
    else:
        flash("Проект создан и привязан к программе.", "success")
        return redirect(url_for("projects.project_detail", project_id=project.id))

    return redirect(url_for("programs.detail", program_id=program_id))


@projects_bp.route("/clone", methods=["GET", "POST"])
def project_clone():
    form = CloneProjectTreeForm()
    form.source_project_id.choices = list_projects_for_clone_choice()

    allowed_ids = {project_id for project_id, _ in form.source_project_id.choices}

    preselected_id_raw = request.args.get("source_project_id", type=int)
    change_source_mode = "change_source" in request.args

    is_preselected = (
        preselected_id_raw in allowed_ids
        and not change_source_mode
    )

    preselected_project = (
        get_project(preselected_id_raw)
        if is_preselected
        else None
    )

    if request.method == "GET":
        if is_preselected and preselected_project is not None:
            form.fixed_source_project_id.data = str(preselected_id_raw)
            form.new_root_title.data = f"{preselected_project.title} (копия)"
        elif preselected_id_raw in allowed_ids:
            form.source_project_id.data = preselected_id_raw
            selected_project = get_project(preselected_id_raw)
            if selected_project is not None:
                form.new_root_title.data = f"{selected_project.title} (копия)"

    if form.validate_on_submit():
        try:
            if form.fixed_source_project_id.data:
                source_project_id = int(form.fixed_source_project_id.data)
            else:
                source_project_id = form.source_project_id.data

            if source_project_id not in allowed_ids:
                raise ValueError("Выберите корректный проект для клонирования.")

            source_project = get_project(source_project_id)
            if source_project is None:
                raise ValueError("Исходный проект не найден.")

            cloned_project = clone_project_tree(
                source_project_id=source_project_id,
                new_root_title=form.new_root_title.data,
            )
        except ValueError as exc:
            flash(str(exc), "error")
        else:
            flash("Поддерево проекта клонировано.", "success")
            return redirect(
                url_for(
                    "projects.project_structure",
                    project_id=cloned_project.id,
                    cloned=1,
                    source_project_id=source_project.id,
                    source_project_title=source_project.title,
                )
            )

    return render_template(
        "projects/clone.html",
        form=form,
        preselected_project=preselected_project,
        is_preselected=is_preselected,
        active_section="projects",
    )


@projects_bp.get("/<int:project_id>")
def project_detail(project_id: int):
    project = get_project(project_id)
    if project is None:
        abort(404)

    child_projects = list_child_projects(project.id)

    return render_template(
        "projects/detail.html",
        project=project,
        child_projects=child_projects,
        active_section="projects",
    )


@projects_bp.route("/<int:project_id>/edit", methods=["GET", "POST"])
def project_edit(project_id: int):
    project = get_project(project_id)
    if project is None:
        abort(404)

    form = ProjectForm()

    if request.method == "GET":
        form.title.data = project.title
        form.description.data = project.description or ""
        form.parent_id.data = str(project.parent_id) if project.parent_id else ""

    if form.validate_on_submit():
        try:
            update_project(
                project_id=project.id,
                title=form.title.data,
                description=form.description.data or "",
            )
        except ValueError as exc:
            flash(str(exc), "error")
        else:
            flash("Проект обновлён.", "success")
            return redirect(url_for("projects.project_detail", project_id=project.id))

    return render_template(
        "projects/edit.html",
        form=form,
        project=project,
        active_section="projects",
    )


@projects_bp.get("/<int:project_id>/structure")
def project_structure(project_id: int):
    project = get_project(project_id)
    if project is None:
        abort(404)

    tree_root = build_project_tree(project.id)

    is_cloned_view = request.args.get("cloned", type=int) == 1
    source_project_id = request.args.get("source_project_id", type=int)
    source_project_title = request.args.get(
        "source_project_title",
        default="",
        type=str,
    )

    return render_template(
        "projects/structure.html",
        project=project,
        tree_root=tree_root,
        is_cloned_view=is_cloned_view,
        source_project_id=source_project_id,
        source_project_title=source_project_title,
        active_section="projects",
    )


@projects_bp.route("/<int:project_id>/children/create", methods=["GET", "POST"])
def project_child_create(project_id: int):
    parent_project = get_project(project_id)
    if parent_project is None:
        abort(404)

    form = ProjectForm()
    form.parent_id.data = str(parent_project.id)

    if form.validate_on_submit():
        try:
            create_project(
                title=form.title.data,
                description=form.description.data or "",
                parent_id=parent_project.id,
                program_id=parent_project.program_id,
            )
        except ValueError as exc:
            flash(str(exc), "error")
        else:
            flash("Дочерний проект создан.", "success")
            return redirect(
                url_for("projects.project_detail", project_id=parent_project.id)
            )

    return render_template(
        "projects/create.html",
        form=form,
        parent_project=parent_project,
        active_section="projects",
    )


@projects_bp.route("/<int:project_id>/attach", methods=["GET", "POST"])
def project_attach_existing(project_id: int):
    project = get_project(project_id)
    if project is None:
        abort(404)

    form = AttachExistingProjectForm()

    available_projects = [
        item for item in list_root_projects()
        if item.id != project.id
    ]
    form.child_project_id.choices = [
        (item.id, item.title) for item in available_projects
    ]

    if form.validate_on_submit():
        try:
            attach_existing_project(
                parent_project_id=project.id,
                child_project_id=form.child_project_id.data,
            )
        except ValueError as exc:
            flash(str(exc), "error")
        else:
            flash("Существующий проект встроен.", "success")
            return redirect(
                url_for("projects.project_structure", project_id=project.id)
            )

    return render_template(
        "projects/attach_existing.html",
        project=project,
        form=form,
        active_section="projects",
    )


@projects_bp.route("/<int:project_id>/move", methods=["GET", "POST"])
def project_move(project_id: int):
    project = get_project(project_id)
    if project is None:
        abort(404)

    form = MoveProjectForm()

    possible_parents = list_possible_parents(project.id)
    form.new_parent_id.choices = [
        (None, "Без родителя"),
        *[(item.id, item.title) for item in possible_parents],
    ]

    if form.validate_on_submit():
        try:
            move_project(
                project_id=project.id,
                new_parent_id=form.new_parent_id.data,
            )
        except ValueError as exc:
            flash(str(exc), "error")
        else:
            flash("Проект перенесён.", "success")
            return redirect(
                url_for("projects.project_structure", project_id=project.id)
            )

    return render_template(
        "projects/move.html",
        project=project,
        form=form,
        active_section="projects",
    )


@projects_bp.post("/<int:project_id>/archive")
def project_archive(project_id: int):
    try:
        archive_project(project_id)
    except ValueError as exc:
        flash(str(exc), "error")
        return redirect(url_for("projects.project_detail", project_id=project_id))

    flash("Проект отправлен в архив.", "success")
    return redirect(url_for("projects.projects_list"))


@projects_bp.post("/<int:project_id>/restore")
def project_restore(project_id: int):
    try:
        restore_project(project_id)
    except ValueError as exc:
        flash(str(exc), "error")
    else:
        flash("Проект восстановлен из архива.", "success")

    return redirect(url_for("projects.project_detail", project_id=project_id))


@projects_bp.route("/<int:project_id>/delete", methods=["GET", "POST"])
def project_delete(project_id: int):
    project = get_project(project_id)
    if project is None:
        abort(404)

    delete_info = can_delete_project(project_id)
    form = DeleteProjectForm()

    if request.method == "GET" and delete_info["has_children"]:
        form.delete_descendants.data = False

    if request.method == "POST":
        if not form.confirm_delete.data:
            flash("Подтвердите удаление проекта.", "error")
        else:
            try:
                if delete_info["has_children"] and not form.delete_descendants.data:
                    raise ValueError(
                        "Для удаления этого проекта нужно подтвердить удаление вложенных элементов."
                    )

                delete_project_with_policy(
                    project_id=project_id,
                    delete_descendants=form.delete_descendants.data,
                )
            except ValueError as exc:
                flash(str(exc), "error")
            else:
                flash("Проект удалён.", "success")
                return redirect(url_for("projects.projects_archive"))

    return render_template(
        "projects/delete_confirm.html",
        project=project,
        delete_info=delete_info,
        form=form,
        active_section="projects",
    )
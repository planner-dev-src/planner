from __future__ import annotations

from flask import abort, flash, redirect, render_template, request, url_for
from flask_wtf import FlaskForm

from . import goals_bp
from .forms import (
    AttachExistingGoalForm,
    CloneGoalTreeForm,
    DeleteGoalForm,
    GoalForm,
    MoveGoalForm,
)
from .services import GoalService
from src.workspaces.services import get_or_create_current_workspace


service = GoalService()


class GoalActionForm(FlaskForm):
    pass


def _resolve_workspace_id() -> str:
    workspace_id = request.args.get("workspace_id", "").strip()
    if workspace_id:
        return workspace_id

    workspace_id = request.form.get("workspace_id", "").strip()
    if workspace_id:
        return workspace_id

    workspace = get_or_create_current_workspace()
    return workspace.id


def _resolve_actor_user_id() -> str:
    return "local-dev-user"


def _build_parent_choices(
    workspace_id: str,
    exclude_goal_id: str | None = None,
) -> list[tuple[str, str]]:
    goals = service.list_parent_choices(
        workspace_id=workspace_id,
        exclude_goal_id=exclude_goal_id,
    )
    choices: list[tuple[str, str]] = [("", "— Без родителя —")]
    choices.extend((goal.id, goal.title) for goal in goals)
    return choices


@goals_bp.get("/")
def goals_list():
    workspace_id = _resolve_workspace_id()
    goals = service.list_root_goals(workspace_id)

    return render_template(
        "goals/list.html",
        goals=goals,
        workspace_id=workspace_id,
        active_section="goals",
    )


@goals_bp.get("/archive")
def goals_archive():
    workspace_id = _resolve_workspace_id()
    goals = service.list_archived_root_goals(workspace_id)
    restore_form = GoalActionForm()

    return render_template(
        "goals/archive.html",
        goals=goals,
        restore_form=restore_form,
        workspace_id=workspace_id,
        active_section="goals",
    )


@goals_bp.route("/create", methods=["GET", "POST"])
def goal_create():
    workspace_id = _resolve_workspace_id()
    form = GoalForm()

    form.workspace_id.data = workspace_id
    form.parent_id.choices = _build_parent_choices(workspace_id)

    parent_goal = None
    requested_parent_id = request.args.get("parent_id", "").strip()

    if request.method == "GET" and requested_parent_id:
        allowed_parent_ids = {value for value, _ in form.parent_id.choices if value}
        if requested_parent_id in allowed_parent_ids:
            form.parent_id.data = requested_parent_id
            parent_goal = service.get_goal(workspace_id, requested_parent_id)

    if form.validate_on_submit():
        try:
            goal = service.create_goal(
                workspace_id=form.workspace_id.data,
                title=form.title.data,
                description=form.description.data,
                kind="goal",
                status=form.status.data,
                priority=form.priority.data,
                parent_id=form.parent_id.data,
                actor_user_id=_resolve_actor_user_id(),
            )
        except ValueError as exc:
            flash(str(exc), "error")
        else:
            flash("Цель создана.", "success")
            return redirect(
                url_for(
                    "goals.goal_detail",
                    goal_id=goal.id,
                    workspace_id=goal.workspace_id,
                )
            )

    return render_template(
        "goals/create.html",
        form=form,
        parent_goal=parent_goal,
        workspace_id=workspace_id,
        active_section="goals",
    )


@goals_bp.route("/clone", methods=["GET", "POST"])
def goal_clone():
    workspace_id = _resolve_workspace_id()

    form = CloneGoalTreeForm()
    form.workspace_id.data = workspace_id
    form.source_goal_id.choices = service.list_goals_for_clone_choice(workspace_id)

    allowed_ids = {goal_id for goal_id, _ in form.source_goal_id.choices}

    preselected_id_raw = request.args.get("source_goal_id", "").strip()
    change_source_mode = "change_source" in request.args

    is_preselected = preselected_id_raw in allowed_ids and not change_source_mode
    preselected_goal = (
        service.get_goal(workspace_id, preselected_id_raw)
        if is_preselected
        else None
    )

    if request.method == "GET":
        if is_preselected and preselected_goal is not None:
            form.fixed_source_goal_id.data = preselected_id_raw
            form.new_root_title.data = f"{preselected_goal.title} (копия)"
        elif preselected_id_raw in allowed_ids:
            form.source_goal_id.data = preselected_id_raw
            selected_goal = service.get_goal(workspace_id, preselected_id_raw)
            if selected_goal is not None:
                form.new_root_title.data = f"{selected_goal.title} (копия)"

    if form.validate_on_submit():
        try:
            source_goal_id = (
                form.fixed_source_goal_id.data
                if form.fixed_source_goal_id.data
                else form.source_goal_id.data
            )

            if source_goal_id not in allowed_ids:
                raise ValueError("Выберите корректную цель для клонирования.")

            source_goal = service.get_goal(workspace_id, source_goal_id)
            if source_goal is None:
                raise ValueError("Исходная цель не найдена.")

            cloned_goal = service.clone_goal_tree(
                workspace_id=workspace_id,
                source_goal_id=source_goal_id,
                new_root_title=form.new_root_title.data,
                actor_user_id=_resolve_actor_user_id(),
            )
        except ValueError as exc:
            flash(str(exc), "error")
        else:
            flash("Поддерево цели клонировано.", "success")
            return redirect(
                url_for(
                    "goals.goal_structure",
                    goal_id=cloned_goal.id,
                    workspace_id=workspace_id,
                    cloned=1,
                    source_goal_id=source_goal.id,
                    source_goal_title=source_goal.title,
                )
            )

    return render_template(
        "goals/clone.html",
        form=form,
        preselected_goal=preselected_goal,
        is_preselected=is_preselected,
        workspace_id=workspace_id,
        active_section="goals",
    )


@goals_bp.get("/<goal_id>")
def goal_detail(goal_id: str):
    workspace_id = _resolve_workspace_id()

    goal = service.get_goal(workspace_id, goal_id)
    if goal is None:
        abort(404)

    child_goals = service.list_child_goals(workspace_id, goal.id)
    archive_form = GoalActionForm()
    restore_form = GoalActionForm()

    return render_template(
        "goals/detail.html",
        goal=goal,
        child_goals=child_goals,
        archive_form=archive_form,
        restore_form=restore_form,
        workspace_id=workspace_id,
        active_section="goals",
    )


@goals_bp.route("/<goal_id>/edit", methods=["GET", "POST"])
def goal_edit(goal_id: str):
    workspace_id = _resolve_workspace_id()

    goal = service.get_goal(workspace_id, goal_id)
    if goal is None:
        abort(404)

    form = GoalForm()
    form.workspace_id.data = workspace_id
    form.parent_id.choices = _build_parent_choices(
        workspace_id=workspace_id,
        exclude_goal_id=goal.id,
    )

    if request.method == "GET":
        form.title.data = goal.title
        form.description.data = goal.description
        form.status.data = goal.status
        form.priority.data = goal.priority
        form.parent_id.data = goal.parent_id or ""

    if form.validate_on_submit():
        try:
            updated_goal = service.update_goal(
                workspace_id=form.workspace_id.data,
                goal_id=goal.id,
                title=form.title.data,
                description=form.description.data,
                kind="goal",
                status=form.status.data,
                priority=form.priority.data,
                parent_id=form.parent_id.data,
                actor_user_id=_resolve_actor_user_id(),
            )
        except ValueError as exc:
            flash(str(exc), "error")
        else:
            flash("Цель обновлена.", "success")
            return redirect(
                url_for(
                    "goals.goal_detail",
                    goal_id=updated_goal.id,
                    workspace_id=updated_goal.workspace_id,
                )
            )

    return render_template(
        "goals/edit.html",
        form=form,
        goal=goal,
        workspace_id=workspace_id,
        active_section="goals",
    )


@goals_bp.get("/<goal_id>/structure")
def goal_structure(goal_id: str):
    workspace_id = _resolve_workspace_id()

    goal = service.get_goal(workspace_id, goal_id)
    if goal is None:
        abort(404)

    tree_root = service.build_goal_tree(workspace_id, goal.id)

    is_cloned_view = request.args.get("cloned", type=int) == 1
    source_goal_id = request.args.get("source_goal_id", default="", type=str)
    source_goal_title = request.args.get("source_goal_title", default="", type=str)

    return render_template(
        "goals/structure.html",
        goal=goal,
        tree_root=tree_root,
        is_cloned_view=is_cloned_view,
        source_goal_id=source_goal_id,
        source_goal_title=source_goal_title,
        workspace_id=workspace_id,
        active_section="goals",
    )


@goals_bp.route("/<goal_id>/children/create", methods=["GET", "POST"])
def goal_child_create(goal_id: str):
    workspace_id = _resolve_workspace_id()

    parent_goal = service.get_goal(workspace_id, goal_id)
    if parent_goal is None:
        abort(404)

    form = GoalForm()
    form.workspace_id.data = workspace_id
    form.parent_id.data = parent_goal.id
    form.parent_id.choices = [(parent_goal.id, parent_goal.title)]

    if form.validate_on_submit():
        try:
            service.create_goal(
                workspace_id=form.workspace_id.data,
                title=form.title.data,
                description=form.description.data,
                kind="goal",
                status=form.status.data,
                priority=form.priority.data,
                parent_id=parent_goal.id,
                actor_user_id=_resolve_actor_user_id(),
            )
        except ValueError as exc:
            flash(str(exc), "error")
        else:
            flash("Дочерняя цель создана.", "success")
            return redirect(
                url_for(
                    "goals.goal_detail",
                    goal_id=parent_goal.id,
                    workspace_id=workspace_id,
                )
            )

    return render_template(
        "goals/create.html",
        form=form,
        parent_goal=parent_goal,
        workspace_id=workspace_id,
        active_section="goals",
    )


@goals_bp.route("/<goal_id>/attach", methods=["GET", "POST"])
def goal_attach_existing(goal_id: str):
    workspace_id = _resolve_workspace_id()

    goal = service.get_goal(workspace_id, goal_id)
    if goal is None:
        abort(404)

    form = AttachExistingGoalForm()
    form.workspace_id.data = workspace_id

    available_goals = [
        item for item in service.list_root_goals(workspace_id)
        if item.id != goal.id
    ]
    form.child_goal_id.choices = [(item.id, item.title) for item in available_goals]

    if form.validate_on_submit():
        try:
            service.attach_existing_goal(
                workspace_id=workspace_id,
                parent_goal_id=goal.id,
                child_goal_id=form.child_goal_id.data,
                actor_user_id=_resolve_actor_user_id(),
            )
        except ValueError as exc:
            flash(str(exc), "error")
        else:
            flash("Существующая цель встроена.", "success")
            return redirect(
                url_for(
                    "goals.goal_structure",
                    goal_id=goal.id,
                    workspace_id=workspace_id,
                )
            )

    return render_template(
        "goals/attach_existing.html",
        goal=goal,
        form=form,
        workspace_id=workspace_id,
        active_section="goals",
    )


@goals_bp.route("/<goal_id>/move", methods=["GET", "POST"])
def goal_move(goal_id: str):
    workspace_id = _resolve_workspace_id()

    goal = service.get_goal(workspace_id, goal_id)
    if goal is None:
        abort(404)

    form = MoveGoalForm()
    form.workspace_id.data = workspace_id

    possible_parents = service.list_possible_parents(workspace_id, goal.id)
    form.new_parent_id.choices = [
        ("", "Без родителя"),
        *[(item.id, item.title) for item in possible_parents],
    ]

    if request.method == "GET":
        form.new_parent_id.data = goal.parent_id or ""

    if form.validate_on_submit():
        try:
            service.move_goal(
                workspace_id=workspace_id,
                goal_id=goal.id,
                new_parent_id=form.new_parent_id.data,
                actor_user_id=_resolve_actor_user_id(),
            )
        except ValueError as exc:
            flash(str(exc), "error")
        else:
            flash("Цель перенесена.", "success")
            return redirect(
                url_for(
                    "goals.goal_structure",
                    goal_id=goal.id,
                    workspace_id=workspace_id,
                )
            )

    return render_template(
        "goals/move.html",
        goal=goal,
        form=form,
        workspace_id=workspace_id,
        active_section="goals",
    )


@goals_bp.post("/<goal_id>/archive")
def goal_archive(goal_id: str):
    workspace_id = _resolve_workspace_id()
    form = GoalActionForm()

    if not form.validate_on_submit():
        flash("Некорректный POST-запрос.", "error")
        return redirect(
            url_for(
                "goals.goal_detail",
                goal_id=goal_id,
                workspace_id=workspace_id,
            )
        )

    try:
        service.archive_goal(
            workspace_id=workspace_id,
            goal_id=goal_id,
            actor_user_id=_resolve_actor_user_id(),
        )
    except ValueError as exc:
        flash(str(exc), "error")
        return redirect(
            url_for(
                "goals.goal_detail",
                goal_id=goal_id,
                workspace_id=workspace_id,
            )
        )

    flash("Цель отправлена в архив.", "success")
    return redirect(url_for("goals.goals_list", workspace_id=workspace_id))


@goals_bp.post("/<goal_id>/restore")
def goal_restore(goal_id: str):
    workspace_id = _resolve_workspace_id()
    form = GoalActionForm()

    if not form.validate_on_submit():
        flash("Некорректный POST-запрос.", "error")
        return redirect(
            url_for(
                "goals.goal_detail",
                goal_id=goal_id,
                workspace_id=workspace_id,
            )
        )

    try:
        service.restore_goal(
            workspace_id=workspace_id,
            goal_id=goal_id,
            actor_user_id=_resolve_actor_user_id(),
        )
    except ValueError as exc:
        flash(str(exc), "error")
    else:
        flash("Цель восстановлена из архива.", "success")

    return redirect(
        url_for(
            "goals.goal_detail",
            goal_id=goal_id,
            workspace_id=workspace_id,
        )
    )


@goals_bp.route("/<goal_id>/delete", methods=["GET", "POST"])
def goal_delete(goal_id: str):
    workspace_id = _resolve_workspace_id()

    goal = service.get_goal(workspace_id, goal_id)
    if goal is None:
        abort(404)

    delete_info = service.can_delete_goal(workspace_id, goal_id)
    form = DeleteGoalForm()
    form.workspace_id.data = workspace_id

    if request.method == "GET" and delete_info["has_children"]:
        form.delete_descendants.data = False

    if form.validate_on_submit():
        if not form.confirm_delete.data:
            flash("Подтвердите удаление цели.", "error")
        else:
            try:
                service.delete_goal_with_policy(
                    workspace_id=workspace_id,
                    goal_id=goal_id,
                    delete_descendants=form.delete_descendants.data,
                    actor_user_id=_resolve_actor_user_id(),
                )
            except ValueError as exc:
                flash(str(exc), "error")
            else:
                flash("Цель удалена.", "success")
                return redirect(
                    url_for("goals.goals_archive", workspace_id=workspace_id)
                )

    return render_template(
        "goals/delete_confirm.html",
        goal=goal,
        delete_info=delete_info,
        form=form,
        workspace_id=workspace_id,
        active_section="goals",
    )
from flask import flash, redirect, render_template, request, url_for

from . import goals_bp
from .forms import GoalForm
from .services import GoalService

service = GoalService()


def _resolve_workspace_id() -> str | None:
    workspace_id = request.args.get("workspace_id", "").strip()
    if workspace_id:
        return workspace_id

    workspace_id = request.form.get("workspace_id", "").strip()
    if workspace_id:
        return workspace_id

    return None


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
    choices = [("", "— Без родителя —")]
    choices.extend((goal.id, goal.title) for goal in goals)
    return choices


@goals_bp.route("/", methods=["GET"])
def list_goals():
    workspace_id = _resolve_workspace_id()
    goals = service.list_goals(workspace_id) if workspace_id else []

    return render_template(
        "goals/list.html",
        goals=goals,
        workspace_id=workspace_id,
        active_section="goals",
    )


@goals_bp.route("/create", methods=["GET", "POST"])
def create_goal():
    workspace_id = _resolve_workspace_id()
    form = GoalForm()

    if workspace_id:
        form.workspace_id.data = workspace_id
        form.parent_id.choices = _build_parent_choices(workspace_id)
    else:
        form.parent_id.choices = [("", "— Сначала выберите workspace —")]

    if form.validate_on_submit():
        try:
            goal = service.create_goal(
                workspace_id=form.workspace_id.data,
                title=form.title.data,
                description=form.description.data,
                kind=form.kind.data,
                status=form.status.data,
                priority=form.priority.data,
                parent_id=form.parent_id.data,
                actor_user_id=_resolve_actor_user_id(),
            )
        except ValueError as exc:
            flash(str(exc), "warning")
        else:
            flash("Цель создана.", "success")
            return redirect(
                url_for("goals.list_goals", workspace_id=goal.workspace_id)
            )

    if request.method == "POST" and not workspace_id:
        flash("Передайте workspace_id в query string или форме.", "warning")

    return render_template(
        "goals/create.html",
        form=form,
        workspace_id=workspace_id,
        active_section="goals",
    )


@goals_bp.route("/<goal_id>/edit", methods=["GET", "POST"])
def edit_goal(goal_id: str):
    workspace_id = _resolve_workspace_id()
    if not workspace_id:
        flash("Передайте workspace_id в query string или форме.", "warning")
        return redirect(url_for("goals.list_goals"))

    goal = service.get_goal(workspace_id, goal_id)
    if goal is None:
        flash("Цель не найдена.", "warning")
        return redirect(url_for("goals.list_goals", workspace_id=workspace_id))

    form = GoalForm()
    form.workspace_id.data = workspace_id
    form.parent_id.choices = _build_parent_choices(
        workspace_id=workspace_id,
        exclude_goal_id=goal.id,
    )

    if request.method == "GET":
        form.title.data = goal.title
        form.description.data = goal.description
        form.kind.data = goal.kind
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
                kind=form.kind.data,
                status=form.status.data,
                priority=form.priority.data,
                parent_id=form.parent_id.data,
                actor_user_id=_resolve_actor_user_id(),
            )
        except ValueError as exc:
            flash(str(exc), "warning")
        else:
            flash("Цель обновлена.", "success")
            return redirect(
                url_for("goals.list_goals", workspace_id=updated_goal.workspace_id)
            )

    return render_template(
        "goals/edit.html",
        form=form,
        goal=goal,
        workspace_id=workspace_id,
        active_section="goals",
    )


@goals_bp.route("/<goal_id>/delete", methods=["POST"])
def delete_goal(goal_id: str):
    workspace_id = _resolve_workspace_id()
    if not workspace_id:
        flash("Передайте workspace_id в форме.", "warning")
        return redirect(url_for("goals.list_goals"))

    try:
        service.delete_goal(
            workspace_id=workspace_id,
            goal_id=goal_id,
            actor_user_id=_resolve_actor_user_id(),
        )
    except ValueError as exc:
        flash(str(exc), "warning")
    else:
        flash("Цель удалена.", "success")

    return redirect(url_for("goals.list_goals", workspace_id=workspace_id))
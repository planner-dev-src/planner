from __future__ import annotations

from flask import flash, redirect, render_template, request, url_for

from . import workspaces_bp
from .services import service


@workspaces_bp.get("/")
def workspaces_list():
    workspaces = service.list_workspaces()
    current_workspace = service.get_or_create_current_workspace()

    return render_template(
        "workspaces/list.html",
        workspaces=workspaces,
        current_workspace=current_workspace,
        active_section="workspaces",
    )


@workspaces_bp.route("/create", methods=["GET", "POST"])
def workspace_create():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        make_default = request.form.get("make_default") == "1"

        try:
            workspace = service.create_workspace(
                name=name,
                is_default=make_default,
            )
        except ValueError as exc:
            flash(str(exc), "error")
        else:
            flash("Workspace создан.", "success")
            return redirect(
                url_for(
                    "workspaces.workspaces_list",
                )
            )

    current_workspace = service.get_or_create_current_workspace()

    return render_template(
        "workspaces/create.html",
        current_workspace=current_workspace,
        active_section="workspaces",
    )


@workspaces_bp.post("/<workspace_id>/set-default")
def workspace_set_default(workspace_id: str):
    try:
        workspace = service.set_default_workspace(workspace_id)
    except ValueError as exc:
        flash(str(exc), "error")
        return redirect(url_for("workspaces.workspaces_list"))

    flash(f"Workspace «{workspace.name}» выбран по умолчанию.", "success")
    return redirect(url_for("workspaces.workspaces_list"))
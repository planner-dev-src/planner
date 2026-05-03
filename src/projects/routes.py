from flask import redirect, render_template, url_for

from . import projects_bp
from .forms import ProjectForm
from .services import create_project, list_projects as get_projects


@projects_bp.route("/")
def list_projects():
    projects = get_projects()
    return render_template("projects/list.html", projects=projects)


@projects_bp.route("/create", methods=["GET", "POST"])
def create_project_view():
    form = ProjectForm()

    if form.validate_on_submit():
        create_project(form.title.data)
        return redirect(url_for("projects.list_projects"))

    return render_template("projects/create.html", form=form)
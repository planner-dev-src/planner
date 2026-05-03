_projects = []
_next_id = 1


def list_projects():
    return _projects


def create_project(title: str):
    global _next_id

    project = {
        "id": _next_id,
        "title": title,
    }
    _projects.append(project)
    _next_id += 1
    return project
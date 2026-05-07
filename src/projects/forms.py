from __future__ import annotations

from typing import Iterable

from flask_wtf import FlaskForm
from wtforms import BooleanField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional


def _coerce_optional_int(value):
    if value in (None, "", "None"):
        return None
    return int(value)


class ProjectForm(FlaskForm):
    title = StringField(
        "Название проекта",
        validators=[
            DataRequired(message="Название проекта обязательно."),
            Length(max=255, message="Название проекта слишком длинное."),
        ],
    )

    description = TextAreaField(
        "Описание",
        validators=[
            Optional(),
            Length(max=5000, message="Описание проекта слишком длинное."),
        ],
    )

    parent_id = SelectField(
        "Родительский проект",
        choices=[],
        coerce=_coerce_optional_int,
        validators=[Optional()],
    )

    program_id = SelectField(
        "Программа",
        choices=[],
        validators=[Optional(), Length(max=64)],
    )

    submit = SubmitField("Создать проект")

    def set_parent_choices(self, projects: Iterable):
        choices = [(None, "Без родительского проекта")]
        choices.extend((project.id, project.title) for project in projects)
        self.parent_id.choices = choices

    def set_program_choices(self, programs: Iterable):
        choices = [("", "Без привязки к программе")]
        choices.extend((program.id, program.title) for program in programs)
        self.program_id.choices = choices


class CloneProjectTreeForm(FlaskForm):
    # Список возможных исходных проектов для клонирования.
    # choices заполняются в роуте list_projects_for_clone_choice().
    source_project_id = SelectField(
        "Исходный проект",
        choices=[],
        coerce=int,
        validators=[Optional()],
    )

    # Используется, когда проект зафиксирован через GET‑параметр
    # и пользователь не должен менять источник.
    fixed_source_project_id = StringField(
        "Зафиксированный исходный проект",
        validators=[Optional()],
    )

    new_root_title = StringField(
        "Название корневого проекта-копии",
        validators=[
            DataRequired(message="Укажите название для корневого проекта-копии."),
            Length(max=255, message="Название проекта слишком длинное."),
        ],
    )

    submit = SubmitField("Клонировать")


class AttachExistingProjectForm(FlaskForm):
    # Список существующих корневых проектов (кроме текущего),
    # которые можно встроить как дочерний.
    child_project_id = SelectField(
        "Существующий проект",
        choices=[],
        coerce=int,
        validators=[DataRequired(message="Выберите проект для встраивания.")],
    )

    submit = SubmitField("Встроить проект")


class MoveProjectForm(FlaskForm):
    # Возможные новые родители для проекта.
    # В роуте в choices первая опция (None, "Без родителя"),
    # далее пары (id, title).
    new_parent_id = SelectField(
        "Новый родитель",
        choices=[],
        coerce=_coerce_optional_int,
        validators=[Optional()],
    )

    submit = SubmitField("Перенести проект")


class DeleteProjectForm(FlaskForm):
    confirm_delete = BooleanField(
        "Я понимаю, что проект будет удалён без возможности восстановления.",
        validators=[DataRequired(message="Нужно подтвердить удаление проекта.")],
    )

    delete_descendants = BooleanField(
        "Удалить все вложенные элементы вместе с этим проектом.",
        validators=[Optional()],
    )

    submit = SubmitField("Удалить проект")
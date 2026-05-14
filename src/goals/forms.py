from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    HiddenField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Length, Optional


STATUS_CHOICES = [
    ("planned", "Запланирована"),
    ("active", "Активная"),
    ("in_progress", "В работе"),
    ("done", "Выполнена"),
    ("cancelled", "Отменена"),
    ("archived", "В архиве"),
]


PRIORITY_CHOICES = [
    ("low", "Низкий"),
    ("medium", "Средний"),
    ("high", "Высокий"),
]


class GoalForm(FlaskForm):
    workspace_id = HiddenField()

    title = StringField(
        "Название",
        validators=[
            DataRequired(message="Введите название цели."),
            Length(max=255),
        ],
    )

    description = TextAreaField(
        "Описание",
        validators=[
            Optional(),
            Length(max=5000),
        ],
    )

    status = SelectField(
        "Статус",
        choices=STATUS_CHOICES,
        validators=[DataRequired(message="Выберите статус.")],
    )

    priority = SelectField(
        "Приоритет",
        choices=PRIORITY_CHOICES,
        validators=[DataRequired(message="Выберите приоритет.")],
    )

    parent_id = SelectField(
        "Родительская цель",
        choices=[],
        validators=[Optional()],
        validate_choice=False,
    )

    submit = SubmitField("Сохранить")


class AttachExistingGoalForm(FlaskForm):
    workspace_id = HiddenField()

    child_goal_id = SelectField(
        "Существующая цель",
        choices=[],
        validators=[DataRequired(message="Выберите цель для присоединения.")],
        validate_choice=False,
    )

    submit = SubmitField("Присоединить")


class MoveGoalForm(FlaskForm):
    workspace_id = HiddenField()

    new_parent_id = SelectField(
        "Новый родитель",
        choices=[],
        validators=[Optional()],
        validate_choice=False,
    )

    submit = SubmitField("Переместить")


class CloneGoalTreeForm(FlaskForm):
    workspace_id = HiddenField()

    source_goal_id = SelectField(
        "Исходная цель",
        choices=[],
        validators=[Optional()],
        validate_choice=False,
    )

    fixed_source_goal_id = HiddenField()

    new_root_title = StringField(
        "Название корневой копии",
        validators=[
            DataRequired(message="Введите название для копии."),
            Length(max=255),
        ],
    )

    submit = SubmitField("Клонировать")


class DeleteGoalForm(FlaskForm):
    workspace_id = HiddenField()

    confirm_delete = BooleanField("Подтверждаю удаление цели.")
    delete_descendants = BooleanField("Удалить также все вложенные элементы")

    submit = SubmitField("Удалить")
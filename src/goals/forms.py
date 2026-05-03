from flask_wtf import FlaskForm
from wtforms import HiddenField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional

GOAL_KIND_CHOICES = [
    ("generic", "Обычная"),
    ("outcome", "Результат"),
    ("milestone", "Этап"),
]

GOAL_STATUS_CHOICES = [
    ("planned", "Запланирована"),
    ("active", "Активна"),
    ("done", "Завершена"),
    ("archived", "В архиве"),
]

GOAL_PRIORITY_CHOICES = [
    ("low", "Низкий"),
    ("normal", "Обычный"),
    ("high", "Высокий"),
]


class GoalForm(FlaskForm):
    workspace_id = HiddenField(
        validators=[DataRequired(message="Workspace обязателен.")]
    )

    title = StringField(
        "Название",
        validators=[
            DataRequired(message="Укажите название цели."),
            Length(max=255, message="Максимум 255 символов."),
        ],
    )

    description = TextAreaField(
        "Описание",
        validators=[
            Optional(),
            Length(max=5000, message="Максимум 5000 символов."),
        ],
    )

    kind = SelectField(
        "Тип",
        choices=GOAL_KIND_CHOICES,
        validators=[DataRequired(message="Выберите тип цели.")],
        default="generic",
    )

    status = SelectField(
        "Статус",
        choices=GOAL_STATUS_CHOICES,
        validators=[DataRequired(message="Выберите статус.")],
        default="planned",
    )

    priority = SelectField(
        "Приоритет",
        choices=GOAL_PRIORITY_CHOICES,
        validators=[DataRequired(message="Выберите приоритет.")],
        default="normal",
    )

    parent_id = SelectField(
        "Родительская цель",
        choices=[],
        validators=[Optional()],
        default="",
    )

    submit = SubmitField("Сохранить")
from datetime import date

from flask_wtf import FlaskForm
from wtforms import HiddenField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.fields import DateField
from wtforms.validators import DataRequired, InputRequired, Length, Optional


PRIORITY_CHOICES = [
    ("low", "Низкий"),
    ("medium", "Средний"),
    ("high", "Высокий"),
]


class AddColumnForm(FlaskForm):
    name = StringField(
        "Название колонки",
        validators=[
            DataRequired(message="Введите название колонки."),
            Length(max=100, message="Название колонки должно быть не длиннее 100 символов."),
        ],
    )
    submit = SubmitField("Добавить колонку")


class EditColumnForm(FlaskForm):
    name = StringField(
        "Название колонки",
        validators=[
            DataRequired(message="Введите название колонки."),
            Length(max=100, message="Название колонки должно быть не длиннее 100 символов."),
        ],
    )
    submit = SubmitField("Сохранить")


class AddTaskForm(FlaskForm):
    title = StringField(
        "Задача",
        validators=[
            DataRequired(message="Введите название задачи."),
            Length(max=255, message="Название задачи должно быть не длиннее 255 символов."),
        ],
    )
    description = TextAreaField(
        "Описание",
        validators=[
            Optional(),
            Length(max=2000, message="Описание должно быть не длиннее 2000 символов."),
        ],
    )
    priority = SelectField(
        "Приоритет",
        choices=PRIORITY_CHOICES,
        default="medium",
        validators=[DataRequired(message="Выберите приоритет.")],
    )
    due_date = DateField(
        "Срок",
        format="%Y-%m-%d",
        validators=[Optional()],
        default=None,
    )
    column_id = HiddenField(
        "Колонка",
        validators=[
            InputRequired(message="Не удалось определить колонку для новой задачи."),
        ],
    )
    submit = SubmitField("Добавить")

    def get_due_date_as_str(self):
        if self.due_date.data is None:
            return None
        if isinstance(self.due_date.data, date):
            return self.due_date.data.isoformat()
        return str(self.due_date.data)


class EditTaskForm(FlaskForm):
    title = StringField(
        "Задача",
        validators=[
            DataRequired(message="Введите название задачи."),
            Length(max=255, message="Название задачи должно быть не длиннее 255 символов."),
        ],
    )
    description = TextAreaField(
        "Описание",
        validators=[
            Optional(),
            Length(max=2000, message="Описание должно быть не длиннее 2000 символов."),
        ],
    )
    priority = SelectField(
        "Приоритет",
        choices=PRIORITY_CHOICES,
        default="medium",
        validators=[DataRequired(message="Выберите приоритет.")],
    )
    due_date = DateField(
        "Срок",
        format="%Y-%m-%d",
        validators=[Optional()],
        default=None,
    )
    column_id = SelectField(
        "Колонка",
        validators=[
            DataRequired(message="Выберите колонку."),
        ],
        choices=[],
    )
    submit = SubmitField("Сохранить")

    def get_due_date_as_str(self):
        if self.due_date.data is None:
            return None
        if isinstance(self.due_date.data, date):
            return self.due_date.data.isoformat()
        return str(self.due_date.data)


class SimplePostForm(FlaskForm):
    submit = SubmitField("OK")
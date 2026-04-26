from flask_wtf import FlaskForm
from wtforms import HiddenField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, InputRequired, Length


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
    column_id = HiddenField(
        "Колонка",
        validators=[
            InputRequired(message="Не удалось определить колонку для новой задачи."),
        ],
    )
    submit = SubmitField("Добавить")


class EditTaskForm(FlaskForm):
    title = StringField(
        "Задача",
        validators=[
            DataRequired(message="Введите название задачи."),
            Length(max=255, message="Название задачи должно быть не длиннее 255 символов."),
        ],
    )
    column_id = SelectField(
        "Колонка",
        validators=[
            DataRequired(message="Выберите колонку."),
        ],
        choices=[],
    )
    submit = SubmitField("Сохранить")


class SimplePostForm(FlaskForm):
    submit = SubmitField("OK")
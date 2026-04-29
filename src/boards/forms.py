from flask_wtf import FlaskForm
from wtforms import DateField, HiddenField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional


PRIORITY_CHOICES = [
    ("low", "Низкий"),
    ("medium", "Средний"),
    ("high", "Высокий"),
]


class AddWorkspaceForm(FlaskForm):
    name = StringField(
        "Название направления",
        validators=[
            DataRequired(message="Введите название направления."),
            Length(max=120, message="Название направления должно быть не длиннее 120 символов."),
        ],
    )
    submit = SubmitField("Создать направление")


class EditWorkspaceForm(FlaskForm):
    name = StringField(
        "Новое название направления",
        validators=[
            DataRequired(message="Введите новое название направления."),
            Length(max=120, message="Название направления должно быть не длиннее 120 символов."),
        ],
    )
    submit = SubmitField("Сохранить")


class AddColumnForm(FlaskForm):
    workspace_id = HiddenField(validators=[DataRequired(message="Не найдено направление для новой колонки.")])
    name = StringField(
        "Название колонки",
        validators=[
            DataRequired(message="Введите название колонки."),
            Length(max=120, message="Название колонки должно быть не длиннее 120 символов."),
        ],
    )
    submit = SubmitField("Добавить колонку")


class EditColumnForm(FlaskForm):
    workspace_id = HiddenField(validators=[DataRequired(message="Не найдено направление колонки.")])
    name = StringField(
        "Новое название колонки",
        validators=[
            DataRequired(message="Введите новое название колонки."),
            Length(max=120, message="Название колонки должно быть не длиннее 120 символов."),
        ],
    )
    submit = SubmitField("Сохранить")


class AddTaskForm(FlaskForm):
    workspace_id = HiddenField(validators=[DataRequired(message="Не найдено направление задачи.")])
    column_id = HiddenField(validators=[DataRequired(message="Не найдена колонка для новой задачи.")])

    title = StringField(
        "Название задачи",
        validators=[
            DataRequired(message="Введите название задачи."),
            Length(max=200, message="Название задачи должно быть не длиннее 200 символов."),
        ],
    )

    description = TextAreaField(
        "Описание",
        validators=[
            Optional(),
            Length(max=5000, message="Описание задачи должно быть не длиннее 5000 символов."),
        ],
    )

    priority = SelectField(
        "Приоритет",
        choices=PRIORITY_CHOICES,
        validators=[DataRequired(message="Выберите приоритет задачи.")],
        default="medium",
    )

    due_date = DateField(
        "Срок",
        format="%Y-%m-%d",
        validators=[Optional()],
    )

    submit = SubmitField("Добавить задачу")


class EditTaskForm(FlaskForm):
    workspace_id = HiddenField(validators=[DataRequired(message="Не найдено направление задачи.")])

    title = StringField(
        "Название задачи",
        validators=[
            DataRequired(message="Введите название задачи."),
            Length(max=200, message="Название задачи должно быть не длиннее 200 символов."),
        ],
    )

    description = TextAreaField(
        "Описание",
        validators=[
            Optional(),
            Length(max=5000, message="Описание задачи должно быть не длиннее 5000 символов."),
        ],
    )

    priority = SelectField(
        "Приоритет",
        choices=PRIORITY_CHOICES,
        validators=[DataRequired(message="Выберите приоритет задачи.")],
        default="medium",
    )

    due_date = DateField(
        "Срок",
        format="%Y-%m-%d",
        validators=[Optional()],
    )

    column_id = SelectField(
        "Колонка",
        choices=[],
        validators=[DataRequired(message="Выберите колонку.")],
    )

    submit = SubmitField("Сохранить")


class SimplePostForm(FlaskForm):
    workspace_id = HiddenField(validators=[Optional()])
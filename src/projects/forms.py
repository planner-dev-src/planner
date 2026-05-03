from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length


class ProjectForm(FlaskForm):
    title = StringField(
        "Название проекта",
        validators=[
            DataRequired(message="Укажите название проекта."),
            Length(max=120, message="Название проекта должно быть не длиннее 120 символов."),
        ],
    )
    submit = SubmitField("Создать проект")
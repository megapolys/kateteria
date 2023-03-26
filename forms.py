from flask_wtf import FlaskForm
from wtforms import PasswordField, BooleanField, SubmitField, StringField, TextAreaField, MultipleFileField
from wtforms.validators import DataRequired


class AdminLoginForm(FlaskForm):
    password = PasswordField('Пароль:', validators=[DataRequired('Введите пароль!')])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class CakeCreateForm(FlaskForm):
    title = StringField('Название:')
    description = TextAreaField('Описание:')
    images = MultipleFileField('Картинки')
    submit = SubmitField('Добавить')

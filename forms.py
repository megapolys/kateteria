from flask_wtf import FlaskForm
from wtforms import PasswordField, BooleanField, SubmitField, StringField, TextAreaField, MultipleFileField, HiddenField
from wtforms.validators import DataRequired


class AdminLoginForm(FlaskForm):
    password = PasswordField('Пароль:', validators=[DataRequired('Введите пароль!')])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class CakeForm(FlaskForm):
    title = StringField('Название:', id='cakeName')
    cake_id = HiddenField(id='cakeId', default=-1)
    description = TextAreaField('Описание:', id='cakeDesc')
    images = MultipleFileField('Картинки')
    submit = SubmitField('Добавить', id='cakeSubmit')

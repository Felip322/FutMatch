import re

from flask_wtf import FlaskForm
from wtforms import BooleanField, DateField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length, ValidationError


class SimpleEmail:
    pattern = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

    def __call__(self, form, field):
        if field.data and not self.pattern.match(field.data):
            raise ValidationError("Informe um e-mail valido.")


class RegisterForm(FlaskForm):
    name = StringField("Nome completo", validators=[DataRequired(), Length(max=120)])
    email = StringField("E-mail", validators=[DataRequired(), SimpleEmail(), Length(max=160)])
    phone = StringField("Telefone", validators=[Length(max=40)])
    birth_date = DateField("Data de nascimento", validators=[DataRequired()])
    city = StringField("Cidade", validators=[DataRequired(), Length(max=100)])
    state = StringField("Estado", validators=[DataRequired(), Length(min=2, max=2)])
    neighborhood = StringField("Bairro", validators=[DataRequired(), Length(max=100)])
    password = PasswordField("Senha", validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField("Confirmação de senha", validators=[DataRequired(), EqualTo("password")])
    accept_terms = BooleanField("Aceito os termos", validators=[DataRequired()])
    submit = SubmitField("Criar conta")


class LoginForm(FlaskForm):
    email = StringField("E-mail", validators=[DataRequired(), SimpleEmail()])
    password = PasswordField("Senha", validators=[DataRequired()])
    remember = BooleanField("Manter conectado")
    submit = SubmitField("Entrar")


class ProfileForm(FlaskForm):
    name = StringField("Nome completo", validators=[DataRequired(), Length(max=120)])
    nickname = StringField("Apelido", validators=[Length(max=80)])
    phone = StringField("Telefone", validators=[Length(max=40)])
    city = StringField("Cidade", validators=[Length(max=100)])
    state = StringField("Estado", validators=[Length(max=2)])
    neighborhood = StringField("Bairro", validators=[Length(max=100)])
    submit = SubmitField("Salvar perfil")


class PasswordChangeForm(FlaskForm):
    current_password = PasswordField("Senha atual", validators=[DataRequired()])
    password = PasswordField("Nova senha", validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField("Confirmação", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Alterar senha")

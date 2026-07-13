from flask_wtf import FlaskForm
from wtforms import BooleanField, HiddenField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length

FLOORS = [("Madeira", "Madeira"), ("Cimento", "Cimento"), ("Sintetico", "Sintetico"), ("Borracha", "Borracha"), ("Grama sintetica", "Grama sintetica")]


class CourtForm(FlaskForm):
    name = StringField("Nome", validators=[DataRequired(), Length(max=140)])
    description = TextAreaField("Descrição")
    address = StringField("Endereço", validators=[DataRequired(), Length(max=180)])
    address_number = StringField("Número")
    city = StringField("Cidade", validators=[DataRequired(), Length(max=100)])
    state = StringField("Estado", validators=[DataRequired(), Length(min=2, max=2)])
    neighborhood = StringField("Bairro")
    zip_code = StringField("CEP")
    latitude = HiddenField("Latitude")
    longitude = HiddenField("Longitude")
    floor_type = SelectField("Tipo de piso", choices=FLOORS)
    is_covered = BooleanField("Coberta")
    size = StringField("Tamanho")
    phone = StringField("Telefone")
    whatsapp = StringField("WhatsApp")
    parking = BooleanField("Estacionamento")
    locker_room = BooleanField("Vestiario")
    shower = BooleanField("Chuveiro")
    snack_bar = BooleanField("Lanchonete")
    bleachers = BooleanField("Arquibancada")
    submit = SubmitField("Salvar quadra")

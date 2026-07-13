from flask_wtf import FlaskForm
from wtforms import HiddenField, IntegerField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, Optional


LEVELS = [("Iniciante", "Iniciante"), ("Recreativo", "Recreativo"), ("Intermediario", "Intermediario"), ("Competitivo", "Competitivo"), ("Avancado", "Avancado")]
CATEGORIES = [("Masculino", "Masculino"), ("Feminino", "Feminino"), ("Misto", "Misto"), ("Base", "Base"), ("Veterano", "Veterano")]
AGE_GROUPS = [("Livre", "Livre"), ("Sub-15", "Sub-15"), ("Sub-17", "Sub-17"), ("Sub-20", "Sub-20"), ("30+", "30+"), ("35+", "35+"), ("40+", "40+")]
FLOORS = [("Madeira", "Madeira"), ("Cimento", "Cimento"), ("Sintetico", "Sintetico"), ("Borracha", "Borracha"), ("Grama sintetica", "Grama sintetica")]


class TeamForm(FlaskForm):
    name = StringField("Nome da equipe", validators=[DataRequired(), Length(max=120)])
    short_name = StringField("Nome abreviado", validators=[Length(max=30)])
    city = StringField("Cidade", validators=[DataRequired(), Length(max=100)])
    state = StringField("Estado", validators=[DataRequired(), Length(min=2, max=2)])
    neighborhood = StringField("Bairro", validators=[Length(max=100)])
    foundation_year = IntegerField("Ano de fundacao", validators=[Optional(), NumberRange(min=1900, max=2100)])
    category = SelectField("Categoria", choices=CATEGORIES)
    age_group = SelectField("Faixa etaria", choices=AGE_GROUPS)
    gender = SelectField("Genero", choices=CATEGORIES)
    skill_level = SelectField("Nivel", choices=LEVELS)
    floor_type = SelectField("Piso preferido", choices=FLOORS)
    description = TextAreaField("Descrição", validators=[Length(max=1000)])
    instagram = StringField("Instagram", validators=[Length(max=120)])
    whatsapp = StringField("WhatsApp", validators=[Length(max=40)])
    home_location = StringField("Local onde costuma jogar", validators=[Length(max=180)])
    home_latitude = HiddenField("Latitude")
    home_longitude = HiddenField("Longitude")
    max_travel_distance = IntegerField("Distancia maxima", validators=[Optional(), NumberRange(min=1, max=200)])
    submit = SubmitField("Salvar equipe")

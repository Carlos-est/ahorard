from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, SubmitField, StringField
from wtforms.validators import Required, DataRequired, Email, Length
from wtforms.fields.html5 import DateField, TimeField
#from wtforms.validators import DataRequired, Email, Length
#from wtforms.fields import DateField, TimeField
from wtforms.fields import html5 as h5fields
from wtforms.widgets import html5 as h5widgets


class FormIndicadoresCultivo(FlaskForm):
    fechaCosecha = DateField('Indique la fecha de la última cosecha realizada, para calcular la fecha aproximada en que se dio la floración:', format='%Y-%m-%d', validators=(DataRequired(),))
    fechaFloracion = DateField('Indique la fecha de floración más reciente, para proyectar la semana óptima de cosecha:', format='%Y-%m-%d', validators=(DataRequired(),))
    nroSemanas = h5fields.IntegerField("Número de semanas:", widget=h5widgets.NumberInput(min=1, max=56), validators=(DataRequired(),))
    fechaFinal = DateField('Fecha final del periodo:', format='%Y-%m-%d', validators=(DataRequired(),))
    
class FormBiomasa(FlaskForm):
    fechaFloracion = DateField('Fecha de la floración más reciente:', format='%Y-%m-%d', validators=(DataRequired(),))
    fechaCosecha = DateField('Indique la fecha de la última cosecha realizada, para calcular el peso potencial que debió alcanzar el racimo:', format='%Y-%m-%d', validators=(DataRequired(),))
    rPa = h5fields.IntegerField("Densidad de plantas de banano por hectárea (1500-2800):", widget=h5widgets.NumberInput(min=1500, max=2800), validators=(DataRequired(),))
    Cant_manos = h5fields.IntegerField("Número de manos:", widget=h5widgets.NumberInput(min=5, max=13), validators=(DataRequired(),))


class FormNutrientes(FlaskForm):
    fechaAplicacion = DateField('Fecha de última aplicación de fertilizante:', format='%Y-%m-%d', validators=(DataRequired(),))
    rPa = h5fields.IntegerField("Densidad de plantas de banano por hectárea (1500-2800):", widget=h5widgets.NumberInput(min=1500, max=2800), validators=(DataRequired(),))
    intervalo = h5fields.IntegerField("Periodo en días entre aplicaciones de fertilizantes:", widget=h5widgets.NumberInput(min=1, max=365), validators=(DataRequired(),))

class FormRiego(FlaskForm):
    dias = h5fields.IntegerField("Número de días que normalmente pasan entre dos riegos (7, 14, 28):", widget=h5widgets.NumberInput(min=7, max=45, step=1), validators=(DataRequired(),))
    fechaFinal = DateField('Fecha final del periodo:', format='%Y-%m-%d', validators=(DataRequired(),))
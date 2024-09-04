from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, DecimalField, SelectField, DateField, IntegerField, FloatField
from wtforms.validators import DataRequired, Email, Length, ValidationError, NumberRange, Optional
from .models import User



class SignupForm(FlaskForm):
    username = StringField('Nombre de Usuario', validators=[DataRequired(), Length(max=64)])
    password = PasswordField('Password', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Registrar')


    def validate_email(self, email):
        # Verificar si el email ya está en uso
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Este correo electrónico ya está registrado.')

    def validate_username(self, username):
        # Verificar si el nombre de usuario ya está en uso
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Este nombre de usuario ya está en uso.')
    
class LoginForm(FlaskForm):
    username = StringField('Nombre de Usuario o Email', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Iniciar Sesión')   



from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, DecimalField, SelectField, DateField, IntegerField, FloatField
from wtforms.validators import DataRequired, Email, Length, ValidationError, NumberRange, Optional, Regexp
#from .models import Fund, Transaction


class DataFilterForm(FlaskForm):
    start_date = DateField('Fecha de inicio', format='%Y-%m-%d', validators=[Optional()])
    end_date = DateField('Fecha final', format='%Y-%m-%d', validators=[Optional()])
    target_percentage = DecimalField('Porcentaje objetivo a ganar', validators=[Optional()])
    submit = SubmitField('Filtrar')

class TransactionForm(FlaskForm):
    #owner = SelectField('Titular', coerce=int, validators=[DataRequired()])
    fund = SelectField('Fondo', coerce=int, validators=[DataRequired()])
    operation = SelectField('Operación', choices=[('first buy', 'Compra inicial'), ('buy', 'Compra'), ('sell', 'Venta'), ('update', 'Actualizar')], validators=[DataRequired()])
    date = DateField('Fecha', format='%Y-%m-%d', validators=[DataRequired()])
    value_per_unit = FloatField('Valor Liquidativo', validators=[DataRequired(), NumberRange(min=-10000, message='El valor puede ser positivo/negativo')])
    units = DecimalField('Número de participaciones', validators=[DataRequired(), NumberRange(min=0)])

class NewFundForm(FlaskForm):
    name = StringField('Nombre del fondo', validators=[DataRequired()])
    contract_number = StringField('Número de contrato', validators=[DataRequired()]) #numero de expediente
    owner = StringField('Titular', validators=[DataRequired()])
    currency = SelectField('Divisa', choices=[('EUR', 'Euros'), ('USD', 'Dólar')], validators=[DataRequired()])  # Nuevo campo
    management_fees = DecimalField('Comisión de gestión', validators=[Optional(), NumberRange(min=0)])
    sell_fees = DecimalField('Comisión de venta', validators=[Optional(), NumberRange(min=0)])
    ter_fees = DecimalField('Comisión TER', validators=[Optional(), NumberRange(min=0)])
    
    ## estos no deben hacer falta, estan en la tabla transactions
    date = DateField('Fecha de compra', validators=[DataRequired()])
    value_per_unit = DecimalField('Valor liquidativo', validators=[DataRequired(), NumberRange(min=0)])
    units = DecimalField('Número de participaciones', validators=[DataRequired(), NumberRange(min=0)])

    submit = SubmitField('Guardar fondo')        


class NewOperationForm(FlaskForm):
    owner = SelectField('Owner', choices=[], validators=[DataRequired()])
    fund = SelectField('Fund', choices=[], validators=[DataRequired()])
    date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])
    operation_type = SelectField('Operation Type', choices=[('first buy', 'Compra inicial'), ('buy', 'Compra'), ('sell', 'Venta'), ('update', 'Actualizar')], validators=[DataRequired()])
    value = DecimalField('Value', validators=[DataRequired()])
    units = DecimalField('Units', validators=[DataRequired()])
    submit = SubmitField('Submit')


class MonthlyReportForm(FlaskForm):
    owner = SelectField('Owner', choices=[], validators=[DataRequired()])
    #start_date = StringField('Start Date', validators=[DataRequired(), Regexp(r'^\d{4}-(0[1-9]|1[0-2])$', message="Please enter a valid date in YYYY-MM format")])
    #end_date = StringField('End Date', validators=[DataRequired(), Regexp(r'^\d{4}-(0[1-9]|1[0-2])$', message="Please enter a valid date in YYYY-MM format")])
    start_date = DateField('Start Date', format='%Y-%m-%d', validators=[DataRequired()], render_kw={"placeholder": "YYYY-MM-DD"})
    end_date = DateField('End Date', format='%Y-%m-%d', validators=[DataRequired()], render_kw={"placeholder": "YYYY-MM-DD"})
    submit = SubmitField('Search')
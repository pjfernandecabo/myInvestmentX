"""
AUTHOR: Pedro
DATE: 21/08/2024
"""
#from flask_login import UserMixin
from sqlalchemy.orm import relationship
#from werkzeug.security import generate_password_hash, check_password_hash

from app import db



class Fund(db.Model):

    __tablename__ = 'funds'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    contract_number = db.Column(db.Integer, nullable=False, unique=True)
    management_fees = db.Column(db.Float, nullable=False)  # Porcentaje de comisiones
    sell_fees = db.Column(db.Float, nullable=False)  # Porcentaje de comisiones
    ter_fees = db.Column(db.Float, nullable=False)  # Porcentaje de comisiones
    currency = db.Column(db.String(10), nullable=False)  # divisa EUR / USD
    owner = db.Column(db.String(50), nullable=False)

    # Relación con la tabla transactions
    transactions = db.relationship('Transaction', backref='fund', lazy=True)
    #transactions = relationship('transactions', backref='fund', lazy=True)


class Transaction(db.Model):

    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    fund_id = db.Column(db.Integer, db.ForeignKey('funds.id'), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # 'buy' o 'sell'
    date = db.Column(db.Date, nullable=False)
    units = db.Column(db.Float, nullable=False)  # Número de participaciones
    value_per_unit = db.Column(db.Float, nullable=False)  # Valor liquidativo por participación

    def total_value(self):
        return self.units * self.value_per_unit

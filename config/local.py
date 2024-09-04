"""
AUTHOR: Pedro
DATE: 07/08/2024
"""

from .default import *


APP_ENV = APP_ENV_LOCAL
SQLALCHEMY_DATABASE_URI = "postgresql://postgres:admin123@172.30.180.88:5432/myfinancex"
CONFIG_SECRET_KEY = SECRET_KEY
#SQLALCHEMY_DATABASE_URI = "postgresql://pedro:1234@localhost:5432/miniblog"

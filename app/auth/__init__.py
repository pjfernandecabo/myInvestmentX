"""

AUTHOR: Pedro
Date: 21/08/2024

"""

from flask import Blueprint

auth_bp = Blueprint('auth', __name__, template_folder='templates')

from . import routes
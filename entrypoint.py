"""
AUTHOR: Pedro
DATE: 07/08/2024
"""

import os
#from flask import send_from_directory
from jinja2 import Undefined

from app import create_app

# settings_module = os.getenv('APP_SETTINGS_MODULE')
settings_module = os.getenv("APP_SETTINGS_MODULE", "config.local")


def format_currency(value):
    if value is None or isinstance(value, Undefined):
        return "N/A"  # Valor por defecto si el valor es None o Undefined
    try:
        return "{:,.2f}".format(float(value)).replace(',', 'X').replace('.', ',').replace('X', '.')
    except (ValueError, TypeError):
        return "N/A"  # Si hay algún otro problema, devolvemos un valor por defecto


app = create_app(settings_module)
# Registrar el filtro en la aplicación de Flask
app.jinja_env.filters['currency'] = format_currency


'''
@app.route('/media/posts/<filename>')
def media_posts(filename):
    dir_path = os.path.join(
        app.config['MEDIA_DIR'],
        app.config['POSTS_IMAGES_DIR'])
    return send_from_directory(dir_path, filename)
'''

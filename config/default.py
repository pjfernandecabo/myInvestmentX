"""
AUTHOR: Pedro
DATE: 11/08/2024
"""

from os.path import abspath, dirname, join


# Define the application directory
BASE_DIR = dirname(dirname(abspath(__file__)))

# Media dir
MEDIA_DIR = join(BASE_DIR, 'static/images')
#print(f"\n\t BASE_DIR = {BASE_DIR}")
#print(f"\n\t MEDIA_DIR = {MEDIA_DIR}")

POSTS_IMAGES_DIR = join(MEDIA_DIR, 'posts')


SECRET_KEY = (
    "7110c8ae51a4b5af97be6534caef90e4bb9bdcb3380af008f90b23a5d1616bf319bc298105da20fe"
)

'''
import secrets
secrets.token_urlsafe(20): I15ybHlvKgwHmYNnzOEl3JI4CjaYyN4OeHhPgVr_pME


'''

# Database configuration
SQLALCHEMY_TRACK_MODIFICATIONS = False

# App environments
APP_ENV_LOCAL = "local"
APP_ENV_TESTING = "testing"
APP_ENV_DEVELOPMENT = "development"
APP_ENV_STAGING = "staging"
APP_ENV_PRODUCTION = "production"
APP_ENV = ""

# Configuración del email
MAIL_SERVER = "tu servidor smtp"
MAIL_PORT = 587
MAIL_USERNAME = "tu correo"
MAIL_PASSWORD = "tu contraseña"
DONT_REPLY_FROM_EMAIL = "dirección from"
ADMINS = ("pedro.fdc@gmail.com",)
MAIL_USE_TLS = True
MAIL_DEBUG = False


ITEMS_PER_PAGE = 3
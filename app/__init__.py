"""
AUTHOR: Pedro
DATE: 07/08/2024
"""
import logging
import time

from flask import Flask, render_template
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from .common.loggers import configure_logging


login_manager = LoginManager()
migrate = Migrate()  # Se crea un objeto de tipo Migrate
db = SQLAlchemy()

def create_app(settings_module):
    app = Flask(__name__, instance_relative_config=True)

    # Load the config file specified by the APP environment variable
    app.config.from_object(settings_module)
    # Load the configuration from the instance folder
    if app.config.get("TESTING", False):
        app.config.from_pyfile("config-testing.py", silent=True)
    else:
        app.config.from_pyfile("config.py", silent=True)
        

    configure_logging(app)


    db.init_app(app)
    migrate.init_app(app, db) #inicializa el objeto migrate

    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)


    from .auth.models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))


    # Registro de los Blueprints
    from .auth import auth_bp
    app.register_blueprint(auth_bp)

    from .admin import admin_bp
    app.register_blueprint(admin_bp)

    from .public import public_bp
    app.register_blueprint(public_bp)

    #from .routes import main as main_blueprint
    #app.register_blueprint(main_blueprint)

    with app.app_context():
        db.create_all()

    return app


    
'''

def setup_logger(log_file=f"app/logs/{time.strftime('%Y%m%d-%H%M%S')}.log"):

    #logging.basicConfig(
    #    filename=f"logs/{time.strftime('%Y%m%d-%H%M%S')}.log",
    #    filemode='a',
    #    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    #    level=logging.INFO
    #)
    # Crear un logger
    logger = logging.getLogger('mi_aplicacion')
    logger.setLevel(logging.DEBUG)

    # Crear un formateador
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Manejador para archivo
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Manejador para consola
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # Puedes ajustar el nivel según tus necesidades
    console_handler.setFormatter(formatter)

    # Agregar los manejadores al logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger



def configure_logging(app):
    # Eliminamos los posibles manejadores, si existen, del logger por defecto
    del app.logger.handlers[:]
    # Añadimos el logger por defecto a la lista de loggers
    loggers = [app.logger, ]
    handlers = []

    #filename=f"app/logs/{time.strftime('%Y%m%d-%H%M%S')}.log"
    logger = setup_logger()



    if (app.config['APP_ENV'] == app.config['APP_ENV_LOCAL']) or (
            app.config['APP_ENV'] == app.config['APP_ENV_TESTING']) or (
            app.config['APP_ENV'] == app.config['APP_ENV_DEVELOPMENT']):
        logger.debug("iniciando Logger en local")
        handlers.append(logger)
    elif app.config['APP_ENV'] == app.config['APP_ENV_PRODUCTION']:
        logger.debug("iniciando Logger en produccion")
        handlers.append(logger)


    # Asociamos cada uno de los handlers a cada uno de los loggers
    for l in loggers:
        for handler in handlers:
            l.addHandler(handler)
        l.propagate = False
        l.setLevel(logging.DEBUG)



def verbose_formatter():
    return logging.Formatter(
        '[%(asctime)s.%(msecs)d]\t %(levelname)s \t[%(name)s.%(funcName)s:%(lineno)d]\t %(message)s',
        datefmt='%d/%m/%Y %H:%M:%S'
    )        


    '''


class LoggingHandler:
    '''
    working perfectly althout I am not using it. Ive changed by setup_logger to try new stuffs 
    '''
    def __init__(self, log_file):
        self.logger = logging.getLogger(__name__)
        c_handler = logging.StreamHandler()
        f_handler = logging.FileHandler(log_file)

        c_handler.setLevel(logging.INFO)
        f_handler.setLevel(logging.INFO)

        # Create formatters and add it to handlers
        c_format = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
        f_format: Formatter = logging.Formatter(
            "[%(levelname)s] - %(asctime)s, filename: %(filename)s, funcname: %(funcName)s, line: %(lineno)s\n messages ---->\n %(message)s"
        )
        c_handler.setFormatter(c_format)
        f_handler.setFormatter(f_format)

        # Add handlers to the logger
        self.logger.addHandler(c_handler)
        self.logger.addHandler(f_handler)

    def get_logger(self):
        return self.logger



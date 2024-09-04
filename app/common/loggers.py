"""
AUTHOR: Pedro
DATE: 23/08/2024
"""
import logging
import time



def setup_logger(log_file=f"app/logs/{time.strftime('%Y%m%d-%H')}.log"):
    '''
    inicializa Logger
    smilar a la clase de abajo LoggingHandler

    Quitamos el fichero log en formato time.strftime('%Y%m%d-%H%M%S') para mas adelante
    '''

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
    console_handler.setLevel(logging.WARNING)  # Puedes ajustar el nivel según tus necesidades
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
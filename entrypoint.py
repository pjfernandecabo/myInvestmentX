"""
AUTHOR: Pedro
DATE: 07/08/2024
"""

import os
#from flask import send_from_directory

from app import create_app


# settings_module = os.getenv('APP_SETTINGS_MODULE')
settings_module = os.getenv("APP_SETTINGS_MODULE", "config.local")

app = create_app(settings_module)

'''
@app.route('/media/posts/<filename>')
def media_posts(filename):
    dir_path = os.path.join(
        app.config['MEDIA_DIR'],
        app.config['POSTS_IMAGES_DIR'])
    return send_from_directory(dir_path, filename)
'''


from flask import abort, render_template, current_app, redirect, url_for, request
from flask_login import current_user

#from app.models import Post, Comment
#from .forms import CommentForm
from . import public_bp
import logging

logger = logging.getLogger(__name__)

@public_bp.route('/')
def index():
    logger.info("Entrando en index")
    return render_template('public/index.html')
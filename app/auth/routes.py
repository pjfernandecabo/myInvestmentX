import logging

from flask import Blueprint, render_template, redirect, url_for, flash, request, Response, jsonify
from flask_login import current_user, login_user, logout_user, login_required
from urllib.parse import urlparse

from .forms import SignupForm, LoginForm 
from . import auth_bp
from .models import User
from .. import db

logger = logging.getLogger(__name__)


################### Login | logout | register ###############################################

@auth_bp.route('/login/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('public.index'))  # Si el usuario ya está autenticado, redirigir al home (o dashboard)

    form = LoginForm()
    if form.validate_on_submit():
        # Buscar al usuario por nombre de usuario o correo electrónico
        user = User.query.filter((User.username == form.username.data) | (User.email == form.username.data)).first()
        
        if user is None or not user.check_password(form.password.data):
            flash('Nombre de usuario o contraseña incorrectos')
            return redirect(url_for('public.index'))

        # Si las credenciales son correctas, iniciar la sesión del usuario
        login_user(user)
        
        # Redirigir a la página que el usuario quería visitar antes de iniciar sesión
        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            #next_page = url_for('public.index')
            next_page = url_for('admin.data_mgt')
        return redirect(next_page)

    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout/')
def logout():
    logout_user()
    return redirect(url_for('public.index'))


@auth_bp.route('/signup/', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    #print(form.validate_on_submit)
    #print(f"\nform = {form}")
    #print(f"\nform.validate_on_submit = {form.validate_on_submit()}")
    if form.validate_on_submit():
        #print(f"{form =}")
        # Crear nuevo usuario
        user = User(username=form.username.data, email=form.email.data)
        #print(f"\nuser = {user}")
        user.set_password(form.password.data)  # Asume que tienes un método para hashear la password
        #print(f"\nuser = {user.username}")
        db.session.add(user)
        db.session.commit()
        #print(f"pase aqui")
        flash('Usuario registrado con éxito')
        return redirect(url_for('auth.login'))
    
    else:
        print(f"form.errors = {form.errors}")
    return render_template('auth/signup.html', form=form)
from datetime import datetime
import locale
import logging

from flask import Blueprint, render_template, redirect, url_for, flash, request, Response, jsonify
from flask_login import current_user, login_user, logout_user, login_required
import pandas as pd
from urllib.parse import urlparse

from . import admin_bp
from .forms import TransactionForm, NewFundForm, NewOperationForm, MonthlyReportForm
from .. import db
from ..common.get_data import GetSQLData2Pandas
from ..common.draw_data import DrawFigures
from ..admin.models import Fund, Transaction

logger = logging.getLogger(__name__)
#locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')  # Ajustar esto según tu localización

def format_number(x, decimal_places=2):
    if pd.isna(x):
        return ''
    
    # Convertir a string con el número de decimales especificado
    formatted = f"{x:,.{decimal_places}f}"
    
    # Reemplazar la coma por un punto para los decimales
    parts = formatted.split(',')
    parts[-1] = parts[-1].replace('.', ',')
    
    # Unir las partes usando punto como separador de miles
    return '.'.join(parts)




@admin_bp.route('/data/', methods=['GET', 'POST'])
@login_required
def data_mgt():
    '''
    function to fill data from the start to finish in the database
    and generate summary of information:

        total balance EUR: number
        total balance USD: number
        scatter plot EUR: from init to day
        scatter plot USD: same
        table with a row for every one fund

    '''


    draw = DrawFigures()
    d2p = GetSQLData2Pandas()
    user_id = current_user.id
    

    df_transactions_by_user = d2p.get_transactions_by_user(current_user.id)
    #print(f"\n{df_transactions_by_user =}")
    logger.debug(f"\n{df_transactions_by_user =}")

    #############################################################################
    # saldo total por usuario y currency con el ultimo UPDATE
    df_global_balance = d2p.calculate_final_balance(df_transactions_by_user)
    #logger.info(f"\n{df_global_balance =}")

    graph_final_balance = draw.generate_final_balance_chart(df_global_balance)
    #############################################################################
    # Sumamos los saldos por divisa
    df_currency_balance = d2p.calculate_total_balances_by_currency(df_global_balance)
    #logger.debug(f"\n{df_currency_balance =}")
    
    # Generamos el gráfico
    graph_currency_balance = draw.generate_currency_balance_chart(df_currency_balance)
    #graph_balance_by_currency = draw.generate_balance_graph_by_currency(df_global_balance)

    #############################################################################
    #ganancia desde el inicio hasta ultima fecha
    df_gain_from_start = d2p.calculate_gain_from_start(df_transactions_by_user)
    #logger.debug(f"\n{df_gain_from_start =}")

    #############################################################################
    # Saldo inicial de cada fondo
    df_initial_balance = d2p.calculate_initial_balance(df_transactions_by_user)
    #logger.debug(f"\n{df_initial_balance =}")


    ############################# table ################################################
    df_initial_table = pd.merge(df_global_balance, df_gain_from_start, on='Fund id', how='outer', suffixes=('', '_y'))
    df_initial_table['Owner'] = df_initial_table['Owner'].fillna(df_initial_table['Owner_y'])
    df_initial_table = df_initial_table.drop(columns=['Owner_y'])
    if 'Fund_y' in df_initial_table.columns:
        df_initial_table = df_initial_table.drop(columns=['Fund_y'])

    logger.debug(f"\n{df_initial_table =}")

    eur_table_title, usd_table_title, eur_table_html, usd_table_html = d2p.calculate_initial_table_data_summary(df_initial_table)

    return render_template('admin/data_summary.html', 
                           eur_table_title=eur_table_title,
                           usd_table_title=usd_table_title,
                           eur_table_html=eur_table_html,
                           usd_table_html=usd_table_html,
                           graph_final_balance=graph_final_balance,
                           graph_currency_balance=graph_currency_balance,
    )




################### Time search ###############################################

@admin_bp.route('/monthly_report/', methods=['GET', 'POST'])
@login_required
def monthly_report():

    user_id = current_user.id
    tables_html = []
    plots_html = []    
    kpis = {}
    draw = DrawFigures()
    d2p = GetSQLData2Pandas()
    form = MonthlyReportForm()
    
    # Cargar los owners en el desplegable
    form.owner.choices = [('all', 'Todos')] + [(owner.owner, owner.owner) for owner in Fund.query.distinct(Fund.owner).all()]

    if request.method == 'POST':
       # Cargar las opciones de fondos según el owner seleccionado en el POST request
        selected_owner = form.owner.data

        # Reconfigurar las opciones del owner en caso de POST para asegurarse que se validen correctamente
        form.owner.choices = [('all', 'Todos')] + [(owner.owner, owner.owner) for owner in db.session.query(Fund.owner).distinct().all()]

        if form.validate_on_submit():
            # Obtener los datos del formulario
            selected_owner = form.owner.data
            start_date = form.start_date.data
            end_date = form.end_date.data

            start_date = datetime.strptime(f"{start_date}", '%Y-%m-%d')
            end_date = datetime.strptime(f"{end_date}", '%Y-%m-%d')
            # Buscar la información en la base de datos
            query = db.session.query(Transaction, Fund).join(Fund, Transaction.fund_id == Fund.id)
            
            if selected_owner != 'all':
                query = query.filter(Fund.owner == selected_owner)

            ### Calculamos TODAS las trx del owner seleccionado #################################################################
            query = query.filter(Transaction.date >= start_date, Transaction.date <= end_date)
            transactions = query.all()

            df_transactions = pd.DataFrame([{
                'fund': fund.name,
                'currency': fund.currency,
                'owner': fund.owner,
                'transaction_type': transaction.transaction_type,
                'date': transaction.date,
                'units': transaction.units,
                'value_per_unit': transaction.value_per_unit
            } for transaction, fund in transactions])
            logger.debug(f"\n{df_transactions =}")

            ########## Calculamos KPIs ###################################################################
            kpis = d2p.calculate_kpis(df_transactions, end_date)
            logger.debug(f"\n{kpis =}")

            ########## Calculamos TABLAS ###################################################################
            df_monthly_balance = d2p.get_monthly_balance(df_transactions, start_date, end_date)
            logger.debug(f"\n{df_monthly_balance =}")

            df_monthly_difference = d2p.calculate_monthly_difference(df_transactions, df_monthly_balance)
            logger.debug(f"\n{df_monthly_difference =}")

            df_monthly_percentage = d2p.calculate_monthly_percentage_change(df_monthly_difference)
            logger.debug(f"\n{df_monthly_percentage =}")

            df_cumulative_percentage = d2p.calculate_cumulative_percentage_change(df_monthly_percentage)
            logger.debug(f"\n{df_cumulative_percentage =}")

            df_annualized_cumulative = d2p.annualize_cumulative_percentage(df_cumulative_percentage, start_date, end_date)
            logger.debug(f"\n{df_annualized_cumulative =}")

            tables_html, plots_html = d2p.calculate_table_monthly_report(df_annualized_cumulative)
            ########## Calculamos GRAFICOS ###################################################################

        else: 
            print(f"{form.errors =}")
    
    return render_template('admin/monthly_report.html', form=form, kpis=kpis, tables_html=tables_html, plots_html=plots_html)

















################### New transaction ###############################################

@admin_bp.route('/new_transaction/', methods=['GET', 'POST'])
@login_required
def new_transaction():

    print("entro en new_transaction")
    form = NewOperationForm()
    user_id = current_user.id
    # Cargar los fondos disponibles en el campo desplegable
    #form.fund.choices = [(fund.id, fund.name) for fund in Fund.query.all()]
    print(f"\n{user_id =}")
    # Cargar los owners en el desplegable
    #form.owner.choices = [(owner.name, owner.name) for owner in Fund.query.distinct(Fund.owner).all()]
    distinct_owners = Fund.query.with_entities(Fund.owner).distinct().all()
    form.owner.choices = [(owner[0], owner[0]) for owner in distinct_owners] 
    print(f"form.owner.choices = {form.owner.choices =}")
    
    if request.method == 'POST':
        # Cargar las opciones de fondos según el owner seleccionado en el POST request
        selected_owner = form.owner.data
        form.fund.choices = [(fund.name, fund.name) for fund in Fund.query.filter_by(owner=selected_owner).all()]

        if form.validate_on_submit():
            print(f"entro?")
            # Buscar el fondo correspondiente
            fund = Fund.query.filter_by(owner=form.owner.data, name=form.fund.data).first()
            print(f"{fund.id =}")
            if fund:
                # Crear la nueva operación
                new_transaction = Transaction(
                    user_id=user_id,
                    fund_id=fund.id,
                    date=form.date.data,
                    transaction_type=form.operation_type.data,
                    value_per_unit=form.value.data,
                    units=form.units.data
                )
                print(f"\n{new_transaction =}")
                print(f"\n{new_transaction.transaction_type =}")
                db.session.add(new_transaction)
                db.session.commit()
                flash('Transacción guardada correctamente.', 'success')

                #print(f"{form =}")
                return redirect(url_for('admin.data_mgt'))  # Redirigir a una página de resumen o posición
            else:
                print(f"Not fund found!")
        else:
            print(f"{form.errors = }")
    return render_template('admin/new_trx.html', form=form)


@admin_bp.route('/get_funds/<owner>')
def get_funds(owner):
    funds = Fund.query.filter_by(owner=owner).all()
    fund_choices = [{'id': fund.id, 'name': fund.name} for fund in funds]
    return jsonify(fund_choices)

################### New Fund ###############################################
@admin_bp.route('/new_fund/', methods=['GET', 'POST'])
@login_required
def new_fund():

    print("entro en new_fund")
    form = NewFundForm()
    if form.validate_on_submit():
        # Crear un nuevo fondo
        new_fund = Fund(
            name=form.name.data,
            contract_number=form.contract_number.data,
            owner=form.owner.data,
            currency=form.currency.data,
            management_fees=form.management_fees.data,
            sell_fees=form.sell_fees.data,
            ter_fees=form.ter_fees.data,
        )
        
        print(f"\n\t{new_fund.name =}")
        db.session.add(new_fund)
        db.session.commit()
        # Crear una nueva transacción vinculada a este fondo
        new_transaction = Transaction(
            date=form.date.data,
            value_per_unit=form.value_per_unit.data,
            units=form.units.data,
            user_id=current_user.id,  # id del usuario logueado
            fund_id=new_fund.id,       # id del fondo recién creado
            transaction_type='first buy'  # Tipo de transacción es 'compra'
        )
        print(f"\n\t{new_transaction.fund_id =}")
        db.session.add(new_transaction)
        db.session.commit()
        flash('Fondo y transacción guardados correctamente.', 'success')
        return redirect(url_for('admin.data_mgt'))  # Redirigir a la pantalla de posición    
    else:
        print(form.errors)
    return render_template('admin/new_fund.html', form=form)



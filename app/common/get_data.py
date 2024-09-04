import base64
from datetime import datetime
import io
from io import BytesIO
import json
import logging

import altair as alt
from markupsafe import Markup
import matplotlib.pyplot as plt
import pandas as pd
from pandas.tseries.offsets import MonthEnd

from .. import db
#from ..auth.forms import SignupForm
from ..admin.models import Fund, Transaction

logger = logging.getLogger(__name__)

class GetSQLData2Pandas:
    
    @staticmethod
    def get_transactions_by_user(user_id):
        '''
        Realizar la consulta para obtener transacciones junto con los detalles del fondo

        '''
        transactions = (db.session.query(Transaction, Fund)
                        .join(Fund, Transaction.fund_id == Fund.id)
                        .filter(Transaction.user_id == user_id)
                        .with_entities(
                            Fund.id.label('Fund id'),
                            Fund.name.label('Fund'),
                            Fund.owner.label('Owner'),
                            Fund.currency.label('Currency'),
                            Transaction.transaction_type.label('Transaction type'),
                            Transaction.date,
                            Transaction.units,
                            Transaction.value_per_unit,
                            (Transaction.units * Transaction.value_per_unit).label('Total Value')
                        )
                        .all())

        # Convertir el resultado a un DataFrame de Pandas
        df = pd.DataFrame(transactions, columns=['Fund id', 'Fund', 'Owner', 'Currency', 'Transaction type', 'Date', 'Units', 'Value per Unit', 'Total Value'])
        
        return df



    # 1. Saldo Final por Fondo
    @staticmethod
    def calculate_final_balance(df):
        '''
        Muestra el saldo ULTIMO x UPDATE
        obtiene el ultimo update del Fund y lo muestra. Corresponde al saldo mas reciente final del Fund
        Si he actualizado un update en Fund, me muestra ese valor

        '''

        # Filtrar las transacciones de tipo 'update'
        df_updates = df[df['Transaction type'] == 'update']
        
        # Verificar si existen transacciones de tipo 'update'
        if not df_updates.empty:
            # Ordenar por fecha y tomar la última transacción de tipo 'update' por fondo
            df_final = df_updates.sort_values('Date').groupby(['Fund id', 'Fund', 'Owner']).last().reset_index()
        else:
            # Si no hay transacciones de tipo 'update', tomar la última transacción disponible por fondo
            df_final = df.sort_values('Date').groupby(['Fund id', 'Fund', 'Owner', 'Currency']).last().reset_index()
        
        # Calcular el saldo final
        df_final['Final Balance'] = df_final['Units'] * df_final['Value per Unit']
        
        ## convertimos Date a string para que la pueda procesar Altair
        df_final['Date'] = pd.to_datetime(df_final['Date'])  # Asegúrate de que la columna 'Date' sea de tipo datetime
        df_final['Date'] = df_final['Date'].dt.strftime('%Y-%m-%d')  # Convertir la columna 'Date' a string
                
        
        # Asegurarse de que las columnas 'Fund', 'Owner' y 'Final Balance' estén en el DataFrame
        return df_final[['Fund id', 'Fund', 'Currency', 'Owner', 'Final Balance', 'Date']]


    @staticmethod
    def calculate_initial_balance(df):
        '''
        Muestra el saldo PRIMERO x BUY
        obtiene el ultimo update del Fund y lo muestra. Corresponde al saldo mas reciente final del Fund
        Si he actualizado un update en Fund, me muestra ese valor

        '''

        # Filtrar las transacciones de tipo 'update'
        df_updates = df[df['Transaction type'] == 'first buy']
        
        # Verificar si existen transacciones de tipo 'update'
        #if not df_updates.empty:
            # Ordenar por fecha y tomar la última transacción de tipo 'update' por fondo
        df_final = df_updates.sort_values('Date').groupby(['Fund id', 'Fund', 'Owner']).first().reset_index()
        #else:
            # Si no hay transacciones de tipo 'update', tomar la última transacción disponible por fondo
        #    df_final = df.sort_values('Date').groupby(['Fund id', 'Fund', 'Owner', 'Currency']).last().reset_index()
        
        # Calcular el saldo final
        df_final['Final Balance'] = df_final['Units'] * df_final['Value per Unit']
        
        ## convertimos Date a string para que la pueda procesar Altair
        df_final['Date'] = pd.to_datetime(df_final['Date'])  # Asegúrate de que la columna 'Date' sea de tipo datetime
        df_final['Date'] = df_final['Date'].dt.strftime('%Y-%m-%d')  # Convertir la columna 'Date' a string
                
        
        # Asegurarse de que las columnas 'Fund', 'Owner' y 'Final Balance' estén en el DataFrame
        return df_final[['Fund id', 'Fund', 'Currency', 'Owner', 'Final Balance', 'Date']]


    @staticmethod
    def calculate_total_balances_by_currency(df_global_balance):
        # Agrupamos por 'Currency' y sumamos los 'Final Balance'
        df_currency_balance = df_global_balance.groupby('Currency')['Final Balance'].sum().reset_index()
        df_currency_balance.columns = ['Currency', 'Total Balance']
        return df_currency_balance




    # 2. Ganancia desde el Inicio hasta la Última Fecha
    @staticmethod
    def calculate_gain_from_start(df):
        # Verificar si hay transacciones de tipo 'update'
        if 'update' in df['Transaction type'].values:
            # Agrupar por fondo para obtener la primera transacción de compra (buy)
            df_buy = df[df['Transaction type'] == 'first buy'].sort_values('Date').groupby('Fund id').first().reset_index()
            
            # Agrupar por fondo para obtener la última transacción de actualización (update)
            df_update = df[df['Transaction type'] == 'update'].sort_values('Date').groupby('Fund id').last().reset_index()
            
            # Realizar un merge entre las transacciones de update y buy usando 'Fund id'
            df_gain = pd.merge(df_update, df_buy, on='Fund id', suffixes=('_update', '_buy'))
            
            # Calcular la ganancia como la diferencia entre el valor final y el valor de compra
            df_gain['Gain'] = (df_gain['Units_update'] * df_gain['Value per Unit_update']) - \
                            (df_gain['Units_buy'] * df_gain['Value per Unit_buy'])
            
            df_gain['Gain_percentage'] = (((df_gain['Units_update'] * df_gain['Value per Unit_update']) / (df_gain['Units_buy'] * df_gain['Value per Unit_buy']))-1 ) * 100
            df_gain['Gain_percentage'] = df_gain['Gain_percentage'].apply(lambda x: f"{x:.2f}%")

            
            # Renombrar columnas y devolver resultado
            return df_gain[['Fund id', 'Fund_update', 'Owner_update', 'Gain', 'Gain_percentage']].rename(columns={'Fund_update': 'Fund', 'Owner_update': 'Owner', 'Gain_percentage': 'Gain Percentage'}).reset_index(drop=True)
        
        else:
            # Si no hay transacciones de tipo 'update', usar la transacción más reciente para calcular la ganancia
            df_last = df.sort_values('Date').groupby('Fund id').last().reset_index()
            
            # Calcular la ganancia como Units * Value per Unit
            df_last['Gain'] = df_last['Units'] * df_last['Value per Unit']
            
            # Renombrar columnas y devolver resultado
            return df_last[['Fund id', 'Fund', 'Owner', 'Gain']].reset_index(drop=True)



    @staticmethod
    def calculate_initial_table_data_summary(df_last_balance):
        '''
        Table of summaries
        '''
        df_table_summary = df_last_balance.drop(columns=['Fund id', 'Date'])
        #logger.debug(f"\n{df_table_summary =}")
        
        # Vamos a separar por divisas
        # Separar en DataFrames por divisa
        df_eur = df_table_summary[df_table_summary['Currency'] == 'EUR'].copy()
        df_usd = df_table_summary[df_table_summary['Currency'] == 'USD'].copy()

        # Calcular los totales para cada DataFrame
        total_eur = df_eur[['Final Balance', 'Gain']].sum()
        total_usd = df_usd[['Final Balance', 'Gain']].sum()

        # Añadir las filas de totales
        #df_eur = df_eur.append({'Fund': 'Total', 'Owner': '', 'Currency': 'EUR', 
        #                        'Final Balance': total_eur['Final Balance'], 'Gain': total_eur['Gain']}, ignore_index=True)
        #df_usd = df_usd.append({'Fund': 'Total', 'Owner': '', 'Currency': 'USD', 
        #                        'Final Balance': total_usd['Final Balance'], 'Units': total_usd['Gain']}, ignore_index=True)




        # Crear la fila de totales como un DataFrame
        total_row_eur = pd.DataFrame({'Fund': ['Total'], 'Owner': [''], 'Currency': ['EUR'], 
                                    'Final Balance': [total_eur['Final Balance']], 'Gain': [total_eur['Gain']], 'Gain Percentage': ['']})

        total_row_usd = pd.DataFrame({'Fund': ['Total'], 'Owner': [''], 'Currency': ['USD'], 
                                    'Final Balance': [total_usd['Final Balance']], 'Gain': [total_usd['Gain']], 'Gain Percentage': ['']})

        # Concatenar la fila de totales al DataFrame original
        df_eur = pd.concat([df_eur, total_row_eur], ignore_index=True)
        df_usd = pd.concat([df_usd, total_row_usd], ignore_index=True)

        # Formatear números con separadores de miles y decimales, y cambiar el formato de las cifras negativas
        df_eur['Final Balance'] = df_eur['Final Balance'].apply(lambda x: f"{x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        df_usd['Final Balance'] = df_usd['Final Balance'].apply(lambda x: f"{x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

        df_eur['Gain'] = df_eur['Gain'].apply(lambda x: f"{x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        df_usd['Gain'] = df_usd['Gain'].apply(lambda x: f"{x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

        #logger.debug(f"\n{df_eur =}")
        #logger.debug(f"\n{df_usd =}")



        # creamos titulo de la tabla con la fecha (esta deberia ser la misma para cada mes que es cuando actualizo)
        selected_date = df_last_balance['Date'].iloc[0]  # Esto selecciona la primera fecha
        eur_table_title = f"Balance de Fondos EUR al {selected_date}"
        usd_table_title = f"Balance de Fondos USD al {selected_date}"


        # Convertimos el DataFrame a una tabla HTML
        eur_table_html = df_eur.to_html(classes='data', index=False, border=0)
        usd_table_html = df_usd.to_html(classes='data', index=False, border=0)

        return eur_table_title, usd_table_title, eur_table_html, usd_table_html


    #####################################################################################
    ############### hasta aqui todo de Summary

    #################### Monthly report
    @staticmethod
    def get_monthly_balance(df, start_date, end_date):
        '''
        Obtenemos el saldo de cada fondo en cada mes:
        - tomamos el ultimo UPDATE del mes que sera el saldo final
        - Si hay un first buy y no hay update, quiere decir que es una compra y se toma ese first buy
        - todavia no trabajamos los sell y buy que pueda haber en el mes
        
        '''
        # Convertir la columna 'date' a datetime y agregar una columna 'month' que represente solo el mes y el año
        df['date'] = pd.to_datetime(df['date'])
        df['month'] = df['date'].dt.to_period('M')

        # Filtrar por el rango de fechas
        df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
        #logger.debug(f"\n{df =}")

        # Crear un rango de todos los meses entre start_date y end_date
        all_months = pd.period_range(start=start_date, end=end_date, freq='M')

        # Calcular 'total_value' como la multiplicación de 'units' y 'value_per_unit'
        df['total_value'] = df['units'] * df['value_per_unit']

        # Obtener el último 'update' de cada mes
        df_updates = df[df['transaction_type'] == 'update'].groupby(['fund', 'currency', 'owner', 'month']).last().reset_index()
        #logger.debug(f"\n{df_updates =}")

        # Obtener la primera 'first_buy' de cada mes si no hay 'update'
        df_first_buy = df[df['transaction_type'] == 'first buy'].groupby(['fund', 'currency', 'owner']).first().reset_index()
        #logger.debug(f"\n{df_first_buy =}")

        # Expandir los meses para asegurarnos de que cada mes esté representado
        df_expanded = pd.DataFrame()
        for _, row in df_first_buy.iterrows():
            fund_months = pd.DataFrame({
                'fund': [row['fund']] * len(all_months),
                'currency': [row['currency']] * len(all_months),
                'owner': [row['owner']] * len(all_months),
                'month': all_months,
                'units': [row['units']] * len(all_months),
                'value_per_unit': [row['value_per_unit']] * len(all_months),
                'total_value': [row['total_value']] * len(all_months)
            })
            # Solo mantener los meses a partir de la primera compra
            fund_months = fund_months[fund_months['month'] >= row['month']]
            df_expanded = pd.concat([df_expanded, fund_months], ignore_index=True)
        #logger.debug(f"\n{df_expanded =}")

        # Combinar 'df_updates' con 'df_expanded'
        df_combined = pd.merge(df_expanded, df_updates, on=['fund', 'currency', 'owner', 'month'], how='left', suffixes=('_first_buy', '_update'))
        #logger.debug(f"\n{df_combined =}")

        # Asignar 'first_buy' solo al primer mes y propagar el valor hacia adelante
        df_combined['total_value_update'] = df_combined.groupby(['fund', 'currency', 'owner'])['total_value_update'].ffill()
        #logger.debug(f"\ndf_combined segundo {df_combined}")
        
        # Rellenar los NaN en 'total_value' con el valor de 'first_buy' solo cuando no haya 'update'
        df_combined['total_value'] = df_combined['total_value_update'].combine_first(df_combined['total_value_first_buy'])
        #logger.debug(f"\ndf_combined 3 {df_combined}")

        # Si hay NaN en 'total_value', eso significa que no hay 'first_buy' ni 'update', lo llenamos con 0
        #df_combined['total_value'].fillna(0, inplace=True)
        df_combined.fillna({'total_value':0}, inplace=True)
        #logger.debug(f"\ndf_combined 4 {df_combined}")

        # Renombrar la columna 'total_value' a 'total value'
        df_combined.rename(columns={'total_value': 'total value'}, inplace=True)

        # Retornar el DataFrame con la columna renombrada
        return df_combined[['fund', 'currency', 'owner', 'month', 'total value']]


    @staticmethod
    def calculate_monthly_difference(df, df_monthly_balance):
        '''
        Opera buy y sell del mes y los quita del saldo mensual para poder calcular la rentabilidad neta
        '''

        df_monthly_balance.rename(columns={'total value': 'total_value'}, inplace=True)

        # Agrupar por mes para obtener el total de buy y sell de cada mes
        df['total_value'] = df['units'] * df['value_per_unit']
        df_buys = df[df['transaction_type'] == 'buy'].groupby(['fund', 'currency', 'owner', 'month'])['total_value'].sum().reset_index(name='total_buy')
        df_sells = df[df['transaction_type'] == 'sell'].groupby(['fund', 'currency', 'owner', 'month'])['total_value'].sum().reset_index(name='total_sell')

        # Unir los DataFrames al balance mensual
        df_combined = df_monthly_balance.merge(df_buys, on=['fund', 'currency', 'owner', 'month'], how='left')
        #logger.debug(f"\ndf_combined 1 {df_combined}")

        df_combined = df_combined.merge(df_sells, on=['fund', 'currency', 'owner', 'month'], how='left')
        #logger.debug(f"\ndf_combined 2 {df_combined}")

        df_combined.fillna(0, inplace=True)
        #logger.debug(f"\ndf_combined 3 {df_combined}")

        # Calcular la diferencia mensual
        df_combined['monthly_difference'] = df_combined['total_value'] - df_combined['total_buy'] + df_combined['total_sell']
        #logger.debug(f"\ndf_combined 4 {df_combined}")

        return df_combined[['fund', 'currency', 'owner', 'month', 'monthly_difference']]


    @staticmethod
    def calculate_monthly_percentage_change(df_monthly_difference):
        df_monthly_difference['monthly_pct_change'] = df_monthly_difference.groupby(['fund', 'currency', 'owner'])['monthly_difference'].pct_change() * 100
        df_monthly_difference.fillna(0, inplace=True)
        
        return df_monthly_difference[['fund', 'currency', 'owner', 'month', 'monthly_difference', 'monthly_pct_change']]


    @staticmethod
    def __calculate_cumulative_percentage_change(df_monthly_difference):
        df_monthly_difference['cumulative_pct_change'] = df_monthly_difference.groupby(['fund', 'currency', 'owner'])['monthly_difference'].apply(lambda x: (x / x.iloc[0]) * 100 - 100)
        
        return df_monthly_difference[['fund', 'currency', 'owner', 'month', 'monthly_difference', 'monthly_pct_change', 'cumulative_pct_change']]

    @staticmethod
    def calculate_cumulative_percentage_change(df_monthly_difference):
        # Calcular el porcentaje acumulado de cambio
        def calc_cumulative_pct_change(group):
            return (group / group.iloc[0]) * 100 - 100

        # Aplicar la función de cambio acumulado por grupo
        df_monthly_difference['cumulative_pct_change'] = df_monthly_difference.groupby(['fund', 'currency', 'owner'])['monthly_difference'].transform(calc_cumulative_pct_change)

        return df_monthly_difference[['fund', 'currency', 'owner', 'month', 'monthly_difference', 'monthly_pct_change', 'cumulative_pct_change']]




    @staticmethod
    def annualize_cumulative_percentage(df_monthly_difference, start_date, end_date):

        #num_months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + 1
        
        # Calcular la diferencia en días entre las fechas
        days_difference = (end_date - start_date).days
        #logger.debug(f"\n{days_difference =}")

        # Convertir días a meses reales
        num_months = days_difference / 30  # No redondeamos este valor
        #logger.debug(f"\n{num_months =}")


        df_monthly_difference['annualized_cumulative_pct'] = df_monthly_difference['cumulative_pct_change'] * (12 / num_months)

        columnas_deseadas = ['fund', 'monthly_difference', 'monthly_pct_change', 'cumulative_pct_change', 'annualized_cumulative_pct']

        # Selecciona las columnas y conviértelas a string
        resultado = df_monthly_difference[columnas_deseadas]
        logger.debug(f"\n{resultado=}")
        #print(f"{resultado =}")

        return df_monthly_difference[['fund', 'currency', 'owner', 'month', 'monthly_difference', 'monthly_pct_change', 'cumulative_pct_change', 'annualized_cumulative_pct']]



    @staticmethod
    def calculate_table_monthly_report(df):
        
        tables_html = []
        plots_html = []

        # Convertir la columna 'month' a string para que sea serializable a JSON
        df['month'] = df['month'].astype(str)


        # Agrupar por fondo
        for fund, group in df.groupby(['fund', 'currency', 'owner']):
            fund_name = fund[0]
            currency = fund[1]
            chart_id = f"chart-{fund_name.replace(' ', '-')}"  # Crear un ID único para cada gráfico

            # Crear la tabla con meses como columnas
            table_data = {
                'Month': group['month'].astype(str).tolist(),
                'Final Balance': group['monthly_difference'].tolist(),
                'Monthly % Change': group['monthly_pct_change'].tolist(),
                'Cumulated Monthly % Change': group['cumulative_pct_change'].tolist(),
                'Annualized % Change': group['annualized_cumulative_pct'].tolist(),
            }

            df_table = pd.DataFrame(table_data)
            logger.debug(f"\n{table_data =}")
            df_table_html = df_table.to_html(index=False, classes='table table-bordered')
            # Agregar tabla al HTML
            tables_html.append(f'<h3>Fund: {fund_name} ({currency})</h3>' + df_table_html)

#        usd_table_html = df_usd.to_html(classes='data', index=False, border=0)

            # Crear el scatter plot
            scatter_plot = alt.Chart(group).mark_line(point=True).encode(
                x=alt.X('month:T', title='Month'),
                y=alt.Y('total value:Q', title='Final Balance'),
                tooltip=[
                alt.Tooltip('month:T', title='Month'),
                alt.Tooltip('total value:Q', title='Final Balance')
            ]
            ).properties(
                title=f'Scatter Plot - {fund_name} ({currency})',
                width=600,
                height=400
            )

            # Convertir el gráfico a JSON
            scatter_plot_json = json.dumps(json.loads(scatter_plot.to_json()), indent=2)

            # Añadir el contenedor del gráfico y el script para renderizarlo
            plots_html.append(
                Markup(f"""
                <h3>Scatter Plot for {fund_name} ({currency})</h3>
                <div id="{chart_id}"></div>
                <script type="text/javascript">
                    var spec = {scatter_plot_json};
                    vegaEmbed('#{chart_id}', spec);
                </script>
                """)
            )


        return tables_html, plots_html









    @staticmethod
    def get_transactions_by_date(transactions, start_date, end_date):
        # Convertir las transacciones en un DataFrame
        data = [{
            'fund': fund.name,
            'currency': fund.currency,
            'owner': fund.owner,
            'transaction_type': transaction.transaction_type,
            'date': transaction.date,
            'units': transaction.units,
            'value_per_unit': transaction.value_per_unit
        } for transaction, fund in transactions]

        df = pd.DataFrame(data)
        logger.debug(f"\n{df =}")


        df['date'] = pd.to_datetime(df['date'])  # Asegúrate de que la columna 'Date' sea de tipo datetime
        #df['date'] = df['date'].dt.strftime('%Y-%m-%d')  # Convertir la columna 'Date' a string
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)

        # Filtrar por el rango de fechas
        df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
        logger.debug(f"\ndf con filtro de fechas = {df}")


        # Calcular el valor total de las transacciones
        df['total_value'] = df['units'] * df['value_per_unit']

        # Agrupar por fondo y propietario para obtener los últimos 'update', 'buy', 'sell', y 'first_buy'
        df_latest_update = df[df['transaction_type'] == 'update'].groupby(['fund', 'currency', 'owner']).last().reset_index()
        df_total_buy = df[df['transaction_type'] == 'buy'].groupby(['fund', 'currency', 'owner'])['total_value'].sum().reset_index()
        df_total_sell = df[df['transaction_type'] == 'sell'].groupby(['fund', 'currency', 'owner'])['total_value'].sum().reset_index()
        df_first_buy = df[df['transaction_type'] == 'first_buy'].groupby(['fund', 'currency', 'owner']).first().reset_index()

        # Combinar todos los DataFrames
        df_combined = df_latest_update.merge(df_total_buy, on=['fund', 'currency', 'owner'], how='left', suffixes=('', '_buy'))
        df_combined = df_combined.merge(df_total_sell, on=['fund', 'currency', 'owner'], how='left', suffixes=('', '_sell'))
        df_combined = df_combined.merge(df_first_buy[['fund', 'currency', 'owner', 'total_value']], on=['fund', 'currency', 'owner'], how='left', suffixes=('', '_first_buy'))
        logger.debug(f"\n{df_combined =}")

        # Rellenar NaN con 0 para evitar problemas de suma
        df_combined.fillna(0, inplace=True)

        # Calcular el saldo final
        df_combined['balance'] = df_combined['total_value'] + df_combined['total_value_buy'] - df_combined['total_value_sell'] - df_combined['total_value_first_buy']
        logger.debug(f"\ndf_combined mas abajo = {df_combined}")

        # Seleccionar las columnas finales que quieres mostrar
        df_result = df_combined[['fund', 'currency', 'owner', 'balance']]
        logger.debug(f"\n{df_result =}")

        # Convertir el DataFrame en un diccionario para su fácil uso en la plantilla HTML
        report_data = df_result.to_dict(orient='records')

        return report_data




    @staticmethod
    def process_transactions_dict(transactions, start_date, end_date):
        '''
        monthly_report 
        '''

        report_data = {}
        
        for transaction, fund in transactions:
            # Clave para agrupar la información
            key = f"{fund.name} ({fund.currency})"
            
            if key not in report_data:
                report_data[key] = {
                    'fund': fund.name,
                    'currency': fund.currency,
                    'owner': fund.owner,
                    'start_date': start_date,
                    'end_date': end_date,
                    'balance': 0,
                    'first_buy': 0,
                    'total_buy': 0,
                    'total_sell': 0,
                    'latest_update': 0
                }
            
            if transaction.transaction_type == 'update':
                report_data[key]['latest_update'] = transaction.value_per_unit * transaction.units
            elif transaction.transaction_type == 'buy':
                report_data[key]['total_buy'] += transaction.value_per_unit * transaction.units
            elif transaction.transaction_type == 'sell':
                report_data[key]['total_sell'] += transaction.value_per_unit * transaction.units
            elif transaction.transaction_type == 'first_buy':
                report_data[key]['first_buy'] = transaction.value_per_unit * transaction.units
        
        for key in report_data:
            report_data[key]['balance'] = (
                report_data[key]['latest_update'] +
                report_data[key]['total_buy'] -
                report_data[key]['total_sell'] -
                report_data[key]['first_buy']
            )
        
        return report_data











    ###################################################################################
    ################ 

    # 3. Saldo Final de Cada Mes
    @staticmethod
    def calculate_monthly_final_balance(df):
        # Asegurarse de que la columna 'Date' sea de tipo datetime
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        
        # Crear una columna 'YearMonth' para agrupar por año y mes
        df['YearMonth'] = df['Date'].dt.to_period('M')

        # Filtrar solo las transacciones de tipo 'update'
        df_updates = df[df['Transaction type'] == 'update']

        # Obtener el último update de cada mes
        df_final_monthly = df_updates.sort_values('Date').groupby(['Fund id', 'YearMonth']).last().reset_index()

        # Calcular el saldo final de cada mes
        df_final_monthly['Final Balance'] = df_final_monthly['Units'] * df_final_monthly['Value per Unit']

        #print(f"\n{df_final_monthly =}")
        
        return df_final_monthly[['Fund id', 'Fund', 'Owner', 'YearMonth', 'Final Balance']]


    # 4. Plusvalía Mensual
    @staticmethod
    def calculate_monthly_gain(df):
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['Month'] = df['Date'].dt.to_period('M')
        df_updates = df[df['Transaction type'] == 'update']
        df_monthly_gain = df_updates.sort_values('Date').groupby(['Fund id', 'Month']).last().reset_index()
        df_monthly_gain['Monthly Gain'] = df_monthly_gain['Units'] * df_monthly_gain['Value per Unit']

        for fund in df['Fund id'].unique():
            for month in df['Month'].unique():
                df_month = df[(df['Fund id'] == fund) & (df['Month'] == month)]
                monthly_buy_sell = df_month[(df_month['Transaction type'] == 'buy') | 
                                            (df_month['Transaction type'] == 'sell')]
                total_buy_sell_value = (monthly_buy_sell['Units'] * monthly_buy_sell['Value per Unit']).sum()
                df_monthly_gain.loc[(df_monthly_gain['Fund id'] == fund) & 
                                    (df_monthly_gain['Month'] == month), 'Monthly Gain'] -= total_buy_sell_value
        return df_monthly_gain[['Fund id','Fund', 'Owner', 'Month', 'Monthly Gain']].reset_index()







    ################################ A PARTIR DE AQUI NO SE DE DONDE SALEN...ESTARIA FUMADO??? ##########
    @staticmethod
    def calculate_global_balance(df):
        '''
        Función para calcular los saldos globales por fondo y por user

        '''
        # Asegurarse de que solo las columnas numéricas se incluyan en la operación de suma
        numeric_cols = df.select_dtypes(include=['number']).columns
        df_grouped = df.groupby(['Fund', 'Owner', 'Currency', 'Transaction type'])[numeric_cols].sum().reset_index()
        return df_grouped


    @staticmethod
    def calculate_net_balance(df_grouped):
        '''
        Función para calcular el saldo neto por fondo, restando 'sell' de 'buy' y distinguiendo las monedas

        '''
        # Crear una tabla dinámica que incluya 'Currency' como parte del índice
        df_pivot = df_grouped.pivot_table(
            index=['Fund id', 'Owner', 'Currency'],
            columns='Transaction type',
            values='Total Value',
            fill_value=0
        )
        
        # Calcular el saldo neto (buy - sell)
        df_pivot['Net Balance'] = df_pivot.get('buy', 0) - df_pivot.get('sell', 0)
        
        # Resetear el índice para que los datos sean más fáciles de manejar
        return df_pivot.reset_index()


    @staticmethod
    def calculate_total_balance(df):
        '''
        Función para calcular el saldo global por usuario, distinguiendo entre monedas

        '''
        # Crear un diccionario para almacenar el saldo total por moneda
        total_balance_by_currency = {}

        # Agrupar los datos por 'Currency'
        grouped = df.groupby('Currency')

        # Calcular el saldo por cada moneda
        for currency, group in grouped:
            total_buy = group[group['Transaction type'] == 'buy']['Total Value'].sum()
            total_sell = group[group['Transaction type'] == 'sell']['Total Value'].sum()
            total_balance_by_currency[currency] = total_buy - total_sell

        return total_balance_by_currency

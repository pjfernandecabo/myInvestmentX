
import base64
import io
from io import BytesIO

import altair as alt
from flask import render_template
import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objs as go
import plotly.io as pio

class DrawFigures:

    @staticmethod
    def generate_final_balance_chart(df_final):
        '''
        bar chart by fund and user
        '''
        chart = alt.Chart(df_final).mark_bar().encode(
            x=alt.X('Fund:N', title='Fondo'),  # Eje X: Nombre del Fondo
            y=alt.Y('Final Balance:Q', title='Saldo Final'),  # Eje Y: Saldo Final
            color='Owner:N',  # Colores diferentes por propietario
            tooltip=['Fund', 'Owner', 'Final Balance']  # Información en el tooltip
        ).properties(
            title='Saldo Final por Fondo',  # Título del gráfico
            width=600,
            height=400
        ).interactive()  # Permitir la interacción (zoom, hover, etc.)

        # Convertir el gráfico en JSON para pasarlo al frontend
        return chart.to_json()

    @staticmethod
    def generate_currency_balance_chart(df_currency_balance):
        chart = alt.Chart(df_currency_balance).mark_bar().encode(
            x=alt.X('Currency:N', title='Currency'),  # Eje X: Divisa (EUR, USD)
            y=alt.Y('Total Balance:Q', title='Total Balance'),  # Eje Y: Saldo Total
            color=alt.condition(
                alt.datum.Currency == 'EUR',  # Condición para el color
                alt.value('blue'),  # Color para EUR
                alt.value('green')  # Color para USD
            ),
            tooltip=['Currency', 'Total Balance']  # Tooltip con información detallada
        ).properties(
            title='Total Balance by Currency',
            width=400,
            height=300
        ).interactive()

        return chart.to_json()


    @staticmethod
    def generate_balance_graph_by_currency(total_balances):
        '''
        Función para generar gráfico de saldo acumulado en EUR y USD usando Altair

        '''
        # Crear DataFrame para Altair
        df = pd.DataFrame({
            'Currency': list(total_balances.keys()),
            'Net Balance': list(total_balances.values())
        })

        # Crear gráfico de barras con Altair
        chart = alt.Chart(df).mark_bar().encode(
            x=alt.X('Currency:N', title='Currency'),
            y=alt.Y('Net Balance:Q', title='Net Balance'),
            color=alt.condition(
                alt.datum.Currency == 'EUR',  # Color diferente para EUR
                alt.value('blue'),            # Color si es EUR
                alt.value('green')            # Color si es otra moneda
            ),
            tooltip=[alt.Tooltip('Currency:N'), alt.Tooltip('Net Balance:Q')]
        ).properties(
            title='Net Balance by Currency',
            width=300,
            height=300
        )

        # Guardar el gráfico como JSON
        chart_json = chart.to_json()

        # Devolver el nombre del archivo para usarlo en la plantilla
        return chart_json


    ################################ Monthly Report #############################

    @staticmethod
    def generate_table_and_plot(df):
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
            df_table_html = df_table.to_html(index=False, classes='table table-bordered')

            # Agregar tabla al HTML
            tables_html.append(f'<h3>Fund: {fund_name} ({currency})</h3>' + df_table_html)

            # Crear el scatter plot
            scatter_plot = alt.Chart(group).mark_line(point=True).encode(
                x=alt.X('month:T', title='Month'),
                y=alt.Y('total value:Q', title='Final Balance'),
                tooltip=['month:T', 'total value:Q']
            ).properties(
                title=f'Scatter Plot - {fund_name} ({currency})',
                width=600,
                height=400
            )

            # Convertir el gráfico en JSON para renderizar en el frontend
            scatter_plot_json = scatter_plot.to_json()
            plots_html.append(f'<h3>Scatter Plot for {fund_name} ({currency})</h3><div id="chart-{fund_name}"></div>')
            
            # JavaScript para renderizar el gráfico
            plots_html.append(f"""
            <script type="text/javascript">
                var spec = {scatter_plot_json};
                vegaEmbed('#chart-{fund_name}', spec);
            </script>
            """)

        return tables_html, plots_html


    ################## MATPLOTLIB ###################################

    @staticmethod
    def generate_balance_graph_matplotlib(total_balances):
        '''
        Función para generar gráfico de saldo acumulado en EUR y USD

        
        '''
        currencies = list(total_balances.keys())
        balances = list(total_balances.values())

        plt.figure(figsize=(8, 6))
        plt.bar(currencies, balances, color=['blue', 'green'])
        plt.xlabel('Currency')
        plt.ylabel('Net Balance')
        plt.title('Net Balance by Currency')

        # Añadir etiquetas encima de las barras para mostrar los valores exactos
        for i, balance in enumerate(balances):
            plt.text(i, balance + 0.05 * balance, f'{balance:.2f}', ha='center', fontsize=12)

        # Convertir la gráfica en una imagen para incrustarla en el HTML
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plt.close()  # Cerramos el gráfico para liberar memoria
        return base64.b64encode(img.getvalue()).decode()


    @staticmethod
    def generate_fund_balance_graph(df_pivot, currency_label="EUR"):
        '''
        Matplotlib
        Función para generar gráfico de saldo neto por fondo

        '''


        plt.figure(figsize=(10, 6))
        plt.bar(df_pivot['Fund'], df_pivot['Net Balance'])
        plt.xlabel('Fund')
        plt.ylabel(f'Net Balance ({currency_label})')
        plt.title(f'Net Balance in Fund  {currency_label}')
        plt.xticks(rotation=45, ha="right")

        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        return base64.b64encode(img.getvalue()).decode()





    ################ MONTHLY_REPORT ###############################
    @staticmethod
    def plot_altair(df):
        # Asegurarse de que 'month' sea de tipo fecha
        df['month'] = pd.to_datetime(df['month'])

        # Crear un gráfico de líneas para cada fondo
        line = alt.Chart(df).mark_line(point=True).encode(
            x=alt.X('month:T', title='Month'),
            y=alt.Y('monthly_difference:Q', title='Monthly Difference (€)'),
            color=alt.Color('fund:N', title='Fund'),  # Colorear por fondo
            tooltip=[alt.Tooltip('fund:N', title='Fund'),
                    alt.Tooltip('monthly_difference:Q', format=',.2f'),
                    alt.Tooltip('monthly_pct_change:Q', title='Percentage Change', format=',.2%')]
        ).properties(
            title='Monthly Difference for Each Fund Over Time',
            width=600,
            height=400
        )
        
        return line.to_html()

    @staticmethod
    def plot_matplotlib(df):
        # Ensure 'month' is treated as a date
        df['month'] = pd.to_datetime(df['month'])
        
        fig, ax = plt.subplots(figsize=(8, 5))
        # Iterar sobre cada fondo para crear una línea
        for fund, group in df.groupby('fund'):
            ax.plot(group['month'], group['monthly_difference'], marker='o', label=fund)
            
            # Añadir etiquetas de cambio porcentual
            for idx, row in group.iterrows():
                ax.annotate(f'{row["monthly_difference"]:.2f}', (row['month'], row['monthly_difference']), 
                            textcoords="offset points", xytext=(0, 10), ha='center')  # Display monthly_difference
                ax.annotate(f'{row["monthly_pct_change"]:.2f}%', (row['month'], row['monthly_difference']), 
                            textcoords="offset points", xytext=(0, 25), ha='center')  # Display monthly_pct_change


        # Configurar ejes y leyenda
        ax.set_xlabel('Month')
        ax.set_ylabel('Monthly Difference (€)')
        ax.set_title('Monthly Difference Over Time by Fund')
        ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), title='Fund')
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Guardar la gráfica como una imagen PNG
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close()
        
        return f'<img src="data:image/png;base64,{img_base64}" />'

    @staticmethod
    def plot_plotly(df):
        # Ensure 'month' is treated as a date
        df['month'] = pd.to_datetime(df['month'])
        
        # Formatear los valores de la columna 'monthly_difference' antes de pasarla al gráfico
        df['formatted_monthly_difference'] = df['monthly_difference'].apply(lambda x: "{:,.2f}".format(x).replace(",", "X").replace(".", ",").replace("X", "."))
        df['formatted_monthly_pct_change'] = df['monthly_pct_change'].apply(lambda x: "{:.2f}%".format(x))

        fig = go.Figure()

        # Iterar sobre cada fondo para crear una línea
        for fund, group in df.groupby('fund'):
            fig.add_trace(go.Scatter(
                #x=group['month'],
                #y=group['monthly_difference'],
                #mode='lines+markers+text',
                #text=group['monthly_difference'],
                #text_monthly_pct_change=group['monthly_pct_change'],
                #textposition="top center",
                #hovertemplate='Month: %{x}<br>Balance: %{y:.2f}<br>% Change: %{text:.2}%',
                #name=f"{fund}",
                x=group['month'],
                y=group['monthly_difference'],
                mode='lines+markers+text',  # Add 'text' mode to show labels
                text=group['formatted_monthly_difference'],  # This will display the monthly_difference values
                textposition="top center",  # You can adjust this to suit your style
                hovertemplate='Month: %{x}<br>Balance: %{y:.2f}<br>change: %{customdata[0]}<extra></extra>',
                #hovertemplate='%{x}: %{y} units<extra></extra>',
                customdata=group[['formatted_monthly_pct_change']],  # Pasar la columna 'monthly_pct_change' como datos personalizados
                name=f"{fund}"
            ))
        
        # Customize layout
        fig.update_layout(
            title='Monthly Difference Over Time',
            xaxis_title='Month',
            yaxis_title='Monthly Difference (€)',
            hovermode='x unified',
            legend_title_text='Fund',
            width=800,
            height=500
        )
        
        return pio.to_html(fig, full_html=False)        
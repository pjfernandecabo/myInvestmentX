        <div class="graph-altair">
            <div id="balance-chart-eur"></div>
                <script src="https://cdn.jsdelivr.net/npm/vega@5"></script>
                <script src="https://cdn.jsdelivr.net/npm/vega-lite@5"></script>
                <script src="https://cdn.jsdelivr.net/npm/vega-embed@6"></script>
                <div id="balance-chart"></div>
  
                <script type="text/javascript">
                    const chartSpec = {{ graph_final_balance | safe }};
                    vegaEmbed('#balance-chart', chartSpec).catch(console.error);
                </script>
        </div>



    <!-- Sección de KPIs -->
    <div class="kpi-section container">
        <!-- Verificamos si existe saldo_actual_eur en el diccionario kpis -->
        {% if kpis.saldo_actual_eur is not none %}
        <div class="kpi-card">
            Saldo Total Fin Periodo EUR: <span>{{ kpis.saldo_actual_eur }}</span>
        </div>
        {% endif %}
        
        <!-- Verificamos si existe saldo_actual_usd en el diccionario kpis -->
        {% if kpis.saldo_actual_usd is not none %}
        <div class="kpi-card">
            Saldo Total Fin Periodo USD: <span>{{ kpis.saldo_actual_usd }}</span>
        </div>
        {% endif %}
        
        <!-- Verificamos si existe saldo_total_inicio_eur en el diccionario kpis -->
        {% if kpis.saldo_total_inicio_eur is not none %}
        <div class="kpi-card">
            Saldo Total Inicio EUR: <span>{{ kpis.saldo_total_inicio_eur }}</span>
        </div>
        {% endif %}
        
        <!-- Verificamos si existe saldo_total_inicio_usd en el diccionario kpis -->
        {% if kpis.saldo_total_inicio_usd is not none %}
        <div class="kpi-card">
            Saldo Total Inicio USD: <span>{{ kpis.saldo_total_inicio_usd }}</span>
        </div>
        {% endif %}
        
        <!-- Si hay más valores en el diccionario, añadir más KPIs dinámicamente -->
    </div>
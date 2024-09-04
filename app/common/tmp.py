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
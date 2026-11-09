// MarketMate Analytics & Plotly Visualizations Engine
function renderPlotlyChart(containerId, chartJson) {
  const container = document.getElementById(containerId);
  if (!container || !chartJson) return;

  try {
    const figure = typeof chartJson === 'string' ? JSON.parse(chartJson) : chartJson;
    const config = {
      responsive: true,
      displayModeBar: false
    };

    Plotly.newPlot(containerId, figure.data, figure.layout, config);

    // Auto resize listener
    window.addEventListener('resize', function () {
      Plotly.Plots.resize(container);
    });
  } catch (err) {
    console.error('Error rendering chart in ' + containerId, err);
  }
}

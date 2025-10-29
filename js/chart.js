let envChart;

function updateChart(temp, humidity) {
  const ctx = document.getElementById('chartCanvas').getContext('2d');
  if (envChart) envChart.destroy();

  envChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Suhu (°C)', 'Kelembapan (%)'],
      datasets: [{
        label: 'Kondisi Lingkungan',
        data: [temp, humidity],
        backgroundColor: ['#00b4d8', '#90e0ef'],
        borderRadius: 10
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, max: 100 },
        x: { grid: { display: false } }
      }
    }
  });
}

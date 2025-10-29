let sensorChart;

function renderChart(sensorData) {
  const ctx = document.getElementById("sensorChart").getContext("2d");
  if (sensorChart) sensorChart.destroy();

  sensorChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: ["CO₂", "PM2.5", "PM10", "VOC", "O₃"],
      datasets: [{
        label: "Kualitas Udara",
        data: sensorData,
        borderColor: "#0078d7",
        tension: 0.3,
        fill: false
      }]
    },
    options: {
      responsive: true,
      scales: { y: { beginAtZero: true } }
    }
  });
}

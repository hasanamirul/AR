const ctx = document.getElementById("chartCanvas").getContext("2d");
let chartData = {
  labels: [],
  datasets: [{
    label: "Suhu (°C)",
    data: [],
    borderWidth: 2
  }]
};

export const envChart = new Chart(ctx, {
  type: "line",
  data: chartData,
  options: {
    scales: {
      y: { beginAtZero: true }
    }
  }
});

export function updateChart(temp) {
  const now = new Date().toLocaleTimeString();
  chartData.labels.push(now);
  chartData.datasets[0].data.push(temp);
  envChart.update();
}

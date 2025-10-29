let chart;
let chartData = [];
let timeLabels = [];

function initChart() {
  const ctx = document.getElementById('chartCanvas').getContext('2d');
  chart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: timeLabels,
      datasets: [{
        label: 'Suhu (°C)',
        data: chartData,
        borderColor: '#3db2ff',
        backgroundColor: 'rgba(61,178,255,0.2)',
        tension: 0.3
      }]
    },
    options: { responsive: true }
  });
}

function updateChart(temp) {
  const time = new Date().toLocaleTimeString();
  if (timeLabels.length > 15) { timeLabels.shift(); chartData.shift(); }
  timeLabels.push(time);
  chartData.push(temp);
  chart.update();
}

function updateAIInsight(temp, hum, air) {
  let msg = "";
  if (temp > 30) msg += "🌡️ Suhu cukup tinggi. Minum air yang cukup. ";
  else if (temp < 20) msg += "🧥 Cuaca dingin, jaga kesehatan.";
  else msg += "✅ Suhu normal.";

  if (hum > 80) msg += " Udara terasa lembap.";
  else if (hum < 40) msg += " Udara kering, waspadai dehidrasi.";

  if (air > 1010) msg += " 🚫 Kualitas udara kurang baik.";
  else msg += " 🌤️ Kualitas udara cukup baik.";

  document.getElementById("aiInsight").innerText = msg;
}

document.addEventListener("DOMContentLoaded", () => {
  initChart();
  document.getElementById("btnSimulasi").addEventListener("click", () => {
    updateAIInsight(28, 60, 1000);
  });
  document.getElementById("btnReal").addEventListener("click", getWeatherData);
});

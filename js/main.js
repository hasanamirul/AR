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
        borderColor: '#00ffc3',
        backgroundColor: 'rgba(0,255,195,0.2)',
        tension: 0.3
      }]
    },
    options: {
      responsive: true,
      scales: {
        x: { display: true },
        y: { beginAtZero: true }
      }
    }
  });
}

function updateSimulasiData() {
  const temp = (20 + Math.random() * 10).toFixed(1);
  const hum = (50 + Math.random() * 20).toFixed(1);
  const air = (60 + Math.random() * 40).toFixed(1);

  document.getElementById("tempValue").innerText = `${temp} °C`;
  document.getElementById("humidityValue").innerText = `${hum} %`;
  document.getElementById("airValue").innerText = `${air} AQI`;

  const time = new Date().toLocaleTimeString();

  if (timeLabels.length > 15) {
    timeLabels.shift();
    chartData.shift();
  }

  timeLabels.push(time);
  chartData.push(temp);
  chart.update();
}

document.addEventListener("DOMContentLoaded", () => {
  initChart();
  let interval = setInterval(updateSimulasiData, 3000);

  document.getElementById("btnSimulasi").addEventListener("click", () => {
    clearInterval(interval);
    interval = setInterval(updateSimulasiData, 3000);
  });

  document.getElementById("btnReal").addEventListener("click", async () => {
    clearInterval(interval);
    await getWeatherData(); // fungsi dari api.js
  });
});

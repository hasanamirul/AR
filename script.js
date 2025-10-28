const API_KEY = "MASUKKAN_API_KEY_MU_DISINI";
const CITY = "Semarang";
const WEATHER_URL = `https://api.openweathermap.org/data/2.5/weather?q=${CITY}&appid=${API_KEY}&units=metric`;
const AIR_URL = `https://api.openweathermap.org/data/2.5/air_pollution?lat=-6.9667&lon=110.4167&appid=${API_KEY}`;

let isSimulating = false;
let chart;
let labels = [];
let tempData = [];
let aqiData = [];

function initChart() {
  const ctx = document.getElementById('envChart').getContext('2d');
  chart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Suhu (°C)',
          data: tempData,
          borderColor: '#00ffc3',
          backgroundColor: 'rgba(0,255,195,0.1)',
          tension: 0.4
        },
        {
          label: 'AQI',
          data: aqiData,
          borderColor: '#ff7f50',
          backgroundColor: 'rgba(255,127,80,0.1)',
          tension: 0.4
        }
      ]
    },
    options: {
      responsive: true,
      scales: {
        x: { display: true },
        y: { beginAtZero: true }
      },
      plugins: { legend: { labels: { color: 'white' } } }
    }
  });
}

async function fetchData() {
  try {
    if (isSimulating) {
      simulateData();
      return;
    }

    const [weatherRes, airRes] = await Promise.all([
      fetch(WEATHER_URL),
      fetch(AIR_URL)
    ]);

    const weatherData = await weatherRes.json();
    const airData = await airRes.json();

    const temp = weatherData.main.temp;
    const humidity = weatherData.main.humidity;
    const aqi = airData.list[0].main.aqi;

    updateUI(temp, humidity, aqi);
  } catch (error) {
    console.error("Gagal mengambil data:", error);
  }
}

function simulateData() {
  const temp = (20 + Math.random() * 10).toFixed(1);
  const humidity = (50 + Math.random() * 30).toFixed(1);
  const aqi = Math.floor(Math.random() * 5) + 1;
  updateUI(temp, humidity, aqi);
}

function updateUI(temp, humidity, aqi) {
  document.getElementById('temperature').textContent = `${temp} °C`;
  document.getElementById('humidity').textContent = `${humidity} %`;
  document.getElementById('aqi').textContent = aqi;

  const overlayText = document.getElementById('overlayText');
  overlayText.textContent = `🌡 ${temp}°C | 💧 ${humidity}% | AQI: ${aqi}`;

  const now = new Date().toLocaleTimeString();
  if (labels.length > 10) {
    labels.shift(); tempData.shift(); aqiData.shift();
  }
  labels.push(now);
  tempData.push(temp);
  aqiData.push(aqi);
  chart.update();
}

async function initCamera() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
    document.getElementById('camera').srcObject = stream;
  } catch (error) {
    console.error("Tidak dapat mengakses kamera:", error);
  }
}

document.getElementById('realBtn').addEventListener('click', () => {
  isSimulating = false;
  fetchData();
});

document.getElementById('simBtn').addEventListener('click', () => {
  isSimulating = true;
  simulateData();
});

window.onload = () => {
  initCamera();
  initChart();
  fetchData();
  setInterval(fetchData, 10000);
};

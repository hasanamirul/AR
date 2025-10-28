let usingFrontCamera = false;
const videoElement = document.getElementById("cameraFeed");

const tempEl = document.getElementById("tempValue");
const humEl = document.getElementById("humidityValue");
const airEl = document.getElementById("airValue");

// Grafik Chart.js
const ctx = document.getElementById("enviroChart").getContext("2d");
const enviroChart = new Chart(ctx, {
  type: "line",
  data: {
    labels: [],
    datasets: [
      {
        label: "Suhu (°C)",
        borderColor: "#ff6666",
        fill: false,
        data: [],
        tension: 0.4
      },
      {
        label: "Kelembapan (%)",
        borderColor: "#66b3ff",
        fill: false,
        data: [],
        tension: 0.4
      },
      {
        label: "Kualitas Udara (AQI)",
        borderColor: "#66cc66",
        fill: false,
        data: [],
        tension: 0.4
      }
    ]
  },
  options: {
    responsive: true,
    plugins: {
      legend: { position: "bottom" }
    },
    scales: {
      y: { beginAtZero: true }
    }
  }
});

function updateChart(temp, hum, air) {
  const now = new Date().toLocaleTimeString();
  enviroChart.data.labels.push(now);
  enviroChart.data.datasets[0].data.push(temp);
  enviroChart.data.datasets[1].data.push(hum);
  enviroChart.data.datasets[2].data.push(air);
  if (enviroChart.data.labels.length > 10) {
    enviroChart.data.labels.shift();
    enviroChart.data.datasets.forEach(ds => ds.data.shift());
  }
  enviroChart.update();
}

// Ambil data nyata
document.getElementById("fetchData").addEventListener("click", () => {
  const apiKey = "MASUKKAN_API_KEY_MU_DISINI";
  const city = "Jakarta";
  fetch(`https://api.openweathermap.org/data/2.5/weather?q=${city}&appid=${apiKey}&units=metric`)
    .then(res => res.json())
    .then(data => {
      const temp = data.main.temp.toFixed(1);
      const hum = data.main.humidity;
      const air = Math.floor(Math.random() * 100);

      tempEl.textContent = temp;
      humEl.textContent = hum;
      airEl.textContent = air;
      updateChart(temp, hum, air);
    })
    .catch(() => alert("Gagal ambil data nyata, pastikan API key benar!"));
});

// Simulasi data
document.getElementById("simulateData").addEventListener("click", () => {
  const temp = (25 + Math.random() * 5).toFixed(1);
  const hum = (50 + Math.random() * 20).toFixed(0);
  const air = Math.floor(Math.random() * 100);

  tempEl.textContent = temp;
  humEl.textContent = hum;
  airEl.textContent = air;
  updateChart(temp, hum, air);
});

// Kamera
async function startCamera() {
  const constraints = {
    video: { facingMode: usingFrontCamera ? "user" : "environment" }
  };
  try {
    const stream = await navigator.mediaDevices.getUserMedia(constraints);
    videoElement.srcObject = stream;
  } catch (err) {
    alert("Gagal mengakses kamera!");
  }
}

document.getElementById("switchCam").addEventListener("click", () => {
  usingFrontCamera = !usingFrontCamera;
  startCamera();
});

startCamera();

let usingFrontCamera = false;
const videoElement = document.getElementById("cameraFeed");

// Ambil data nyata (OpenWeatherMap)
document.getElementById("fetchData").addEventListener("click", () => {
  const apiKey = "MASUKKAN_API_KEY_MU_DISINI";
  const city = "Jakarta";
  fetch(`https://api.openweathermap.org/data/2.5/weather?q=${city}&appid=${apiKey}&units=metric`)
    .then(res => res.json())
    .then(data => {
      document.getElementById("tempValue").textContent = data.main.temp.toFixed(1);
      document.getElementById("humidityValue").textContent = data.main.humidity;
      document.getElementById("airValue").textContent = Math.floor(Math.random() * 100);
    })
    .catch(() => alert("Gagal mengambil data, pastikan API Key valid!"));
});

// Tombol simulasi data
document.getElementById("simulateData").addEventListener("click", () => {
  document.getElementById("tempValue").textContent = (25 + Math.random() * 5).toFixed(1);
  document.getElementById("humidityValue").textContent = (50 + Math.random() * 20).toFixed(0);
  document.getElementById("airValue").textContent = Math.floor(Math.random() * 100);
});

// Jalankan kamera
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

// Tombol ganti kamera
document.getElementById("switchCam").addEventListener("click", () => {
  usingFrontCamera = !usingFrontCamera;
  startCamera();
});

// Jalankan awal
startCamera();

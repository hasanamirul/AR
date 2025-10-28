let currentFacingMode = "environment";
let stream;

async function startCamera() {
  if (stream) {
    stream.getTracks().forEach(track => track.stop());
  }

  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: currentFacingMode },
      audio: false
    });
    const video = document.getElementById("cameraFeed");
    video.srcObject = stream;
  } catch (err) {
    alert("Gagal mengakses kamera: " + err.message);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  startCamera();

  document.getElementById("switchCamera").addEventListener("click", () => {
    currentFacingMode = currentFacingMode === "environment" ? "user" : "environment";
    startCamera();
  });

  // simulasi update data lingkungan tiap 5 detik
  setInterval(() => {
    document.getElementById("arTemp").innerText = `🌡️ Suhu: ${(25 + Math.random() * 5).toFixed(1)} °C`;
    document.getElementById("arHum").innerText = `💧 Kelembapan: ${(60 + Math.random() * 10).toFixed(1)} %`;
    document.getElementById("arAir").innerText = `🌫️ Kualitas Udara: ${(80 + Math.random() * 5).toFixed(1)} AQI`;
  }, 5000);
});

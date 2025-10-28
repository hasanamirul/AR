const API_KEY = "MASUKKAN_API_KEY_MU_DI_SINI"; 
const CITY = "Semarang";
const tempEl = document.getElementById("temp");
const airEl = document.getElementById("air");
const arButton = document.getElementById("arButton");
const sensorModel = document.getElementById("sensorModel");

// 🔊 Efek suara
const beep = new Audio("assets/beep.mp3");

async function getWeatherData() {
  try {
    const response = await fetch(`https://api.openweathermap.org/data/2.5/weather?q=${CITY}&appid=${API_KEY}&units=metric`);
    const data = await response.json();

    const suhu = data.main.temp.toFixed(1);
    const kualitasUdara = suhu > 33 ? "Buruk" : "Baik";

    tempEl.textContent = suhu;
    airEl.textContent = kualitasUdara;

    if (kualitasUdara === "Buruk") beep.play();

    // Animasi model 3D berdasarkan suhu
    const scale = suhu / 30;
    sensorModel.setAttribute("scale", `${scale} ${scale} ${scale}`);
  } catch (error) {
    console.error("Gagal memuat data:", error);
  }
}

arButton.addEventListener("click", () => {
  sensorModel.setAttribute("visible", true);
  getWeatherData();
  setInterval(getWeatherData, 10000); // update tiap 10 detik
});

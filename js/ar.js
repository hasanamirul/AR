const API_KEY = "MASUKKAN_API_KEY_MU_DISINI";
const CITY = "Semarang";

async function getWeatherDataAR() {
  const res = await fetch(`https://api.openweathermap.org/data/2.5/weather?q=${CITY}&appid=${API_KEY}&units=metric&lang=id`);
  const data = await res.json();

  const suhu = data.main.temp;
  const kelembapan = data.main.humidity;
  const kondisi = data.weather[0].description;

  const el = document.querySelector("#weatherText");
  el.setAttribute("text", `value: 🌡️ ${suhu}°C | 💧 ${kelembapan}% | ${kondisi}; color: #00FFAA; align: center;`);
}

getWeatherDataAR();
setInterval(getWeatherDataAR, 60000);

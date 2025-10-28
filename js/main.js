import { getAIInsight } from './ai_insight.js';
import { updateChart } from './chart.js';

const API_KEY = "MASUKKAN_API_KEY_MU";
const CITY = "Semarang";
const tempEl = document.getElementById("temp");
const airEl = document.getElementById("air");
const humidityEl = document.getElementById("humidity");
const insightEl = document.getElementById("ai-insight");
const beep = new Audio("assets/sound/beep.mp3");

async function getWeather() {
  const response = await fetch(`https://api.openweathermap.org/data/2.5/weather?q=${CITY}&appid=${API_KEY}&units=metric`);
  const data = await response.json();
  return {
    temp: data.main.temp,
    humidity: data.main.humidity
  };
}

async function getLocalIoT() {
  try {
    const res = await fetch("http://192.168.0.10/data.json"); // data dari NodeMCU
    return await res.json();
  } catch {
    return null;
  }
}

async function refreshData() {
  const weather = await getWeather();
  const local = await getLocalIoT();

  const temp = local?.temp || weather.temp;
  const humidity = local?.humidity || weather.humidity;
  const airQuality = temp > 33 ? "Buruk" : "Baik";

  tempEl.textContent = temp.toFixed(1);
  humidityEl.textContent = humidity.toFixed(0);
  airEl.textContent = airQuality;

  if (airQuality === "Buruk") beep.play();

  updateChart(temp);
  insightEl.textContent = getAIInsight(temp, airQuality, humidity);
}

document.getElementById("refreshBtn").addEventListener("click", refreshData);
refreshData();
setInterval(refreshData, 10000);

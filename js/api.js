const API_KEY = "d629ed8416f6ccdf4075a3407a5970fd";
const city = "Semarang";

async function getWeatherData() {
  const res = await fetch(`https://api.openweathermap.org/data/2.5/weather?q=${city}&appid=${API_KEY}&units=metric&lang=id`);
  const data = await res.json();
  return data;
}

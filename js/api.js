const apiKey = "d629ed8416f6ccdf4075a3407a5970fd";
const defaultCity = "Semarang";

async function fetchWeather(city = defaultCity) {
  const res = await fetch(`https://api.openweathermap.org/data/2.5/weather?q=${city}&units=metric&lang=id&appid=${apiKey}`);
  const data = await res.json();
  return {
    temp: data.main.temp.toFixed(1),
    humidity: data.main.humidity,
    air: data.weather[0].description
  };
}

async function init() {
  const weather = await fetchWeather();
  document.getElementById("temp").innerText = weather.temp;
  document.getElementById("humidity").innerText = weather.humidity;
  document.getElementById("air").innerText = weather.air;

  const insight = getAIInsight(weather.temp, weather.humidity, weather.air);
  document.getElementById("insight").innerText = insight;

  updateChart(weather.temp, weather.humidity);
}

window.addEventListener("load", () => {
  init();
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('sw.js');
  }
});

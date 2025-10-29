(async function () {
  const weatherData = await getWeatherData();

  const suhu = weatherData.main.temp;
  const kondisi = weatherData.weather[0].description;
  const kualitasUdara = Math.floor(Math.random() * 150); // simulasi sensor

  document.getElementById("suhu").innerText = `Suhu: ${suhu.toFixed(1)}°C`;
  document.getElementById("kondisi").innerText = `Kondisi: ${kondisi}`;
  document.getElementById("aqi").innerText = `Indeks Kualitas Udara: ${kualitasUdara}`;

  // Chart
  renderChart([90, 70, 60, 80, 100]);

  // Insight AI
  const insight = getAIInsight(suhu, kualitasUdara);
  document.getElementById("ai-insight").innerText = insight;

  // Audio jika kondisi buruk
  if (suhu > 30 || kualitasUdara > 100) {
    const beep = new Audio("assets/beep.mp3");
    beep.play();
  }
})();

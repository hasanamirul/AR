async function getWeatherData() {
  const apiKey = "MASUKKAN_API_KEY_MU_DISINI"; // ← ganti dengan API key kamu
  const city = "Semarang";

  try {
    const res = await fetch(
      `https://api.openweathermap.org/data/2.5/weather?q=${city}&appid=${apiKey}&units=metric&lang=id`
    );
    const data = await res.json();

    const suhu = data.main.temp;
    const kelembapan = data.main.humidity;
    const tekanan = data.main.pressure;
    const kondisi = data.weather[0].description;

    document.getElementById("tempValue").innerText = `${suhu} °C`;
    document.getElementById("humidityValue").innerText = `${kelembapan} %`;
    document.getElementById("airValue").innerText = `${tekanan} hPa`;

    // update grafik
    chartData.push(suhu);
    timeLabels.push(new Date().toLocaleTimeString());
    chart.update();
  } catch (err) {
    alert("❌ Gagal mengambil data cuaca. Pastikan API key valid.");
    console.error(err);
  }
}

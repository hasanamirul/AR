function getAIInsight(temp, humidity, air) {
  const beep = document.getElementById("alertSound");
  let msg = "";

  if (temp > 32) {
    msg = "⚠️ Suhu tinggi! Hindari aktivitas berat di luar ruangan.";
    beep.play();
  } else if (temp < 20) {
    msg = "🌡️ Cuaca dingin, jaga suhu tubuhmu.";
  } else if (air.includes("hujan")) {
    msg = "☔ Hujan terdeteksi, bawa payung ya!";
  } else if (humidity > 80) {
    msg = "💧 Kelembapan tinggi, jaga ventilasi ruangan.";
  } else {
    msg = "✅ Lingkungan dalam kondisi ideal dan nyaman.";
  }

  return msg;
}

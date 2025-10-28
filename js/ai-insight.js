export function getAIInsight(temp, air, humidity) {
  if (air === "Buruk" && temp > 32) {
    return "⚠️ Udara panas dan tidak sehat. Disarankan menutup jendela dan menyalakan ventilasi.";
  } else if (humidity < 40) {
    return "💧 Udara kering. Disarankan menggunakan humidifier.";
  } else if (temp < 20) {
    return "🧥 Cuaca dingin, gunakan pakaian hangat.";
  } else {
    return "✅ Kondisi lingkungan normal dan nyaman.";
  }
}

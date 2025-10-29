function getAIInsight(temp, airQuality) {
  if (temp > 30) return "🌞 Suhu cukup tinggi hari ini. Tetap terhidrasi dan hindari aktivitas berat di luar ruangan.";
  if (airQuality > 100) return "🌫️ Kualitas udara kurang baik. Disarankan memakai masker jika keluar rumah.";
  return "🌿 Kondisi lingkungan stabil. Nikmati hari Anda!";
}

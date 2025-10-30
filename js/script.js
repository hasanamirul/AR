import { dummyData } from './dummy-data.js';
import { createChart, pushData } from './chart.js';

const chart = createChart();

// Update UI when dummy data changes
function onSensorUpdate(data) {
  // Update cards
  const suhuEl = document.getElementById('suhu');
  const kondisiEl = document.getElementById('kondisi');
  const aqiEl = document.getElementById('aqi');
  const humEl = document.getElementById('humidity');
  const aiEl = document.getElementById('ai-insight');

  if (suhuEl) suhuEl.textContent = `${data.temperature.toFixed(1)}°C`;
  if (kondisiEl) kondisiEl.textContent = data.weather;
  if (aqiEl) aqiEl.textContent = `AQI: ${Math.round(data.aqi)}`;
  if (humEl) humEl.textContent = `Kelembapan: ${Math.round(data.humidity)}%`;

  // Simple AI insight
  let insight = '';
  if (data.temperature > 30) insight = 'Suhu tinggi — hindari aktivitas fisik berat.';
  else if (data.temperature < 23) insight = 'Suhu rendah — pertimbangkan pakaian hangat.';
  else insight = 'Suhu nyaman untuk beraktivitas.';
  if (data.aqi > 100) insight += ' Kualitas udara kurang baik, gunakan masker.';
  if (aiEl) aiEl.textContent = insight;

  // Update chart
  pushData(chart, { temperature: parseFloat(data.temperature.toFixed(1)), aqi: Math.round(data.aqi) });
}

// Subscribe to dummy data generator
dummyData.subscribe(onSensorUpdate);

// Export nothing; script runs automatically when imported as module in index.html

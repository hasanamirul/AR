function renderChart(data) {
  const ctx = document.getElementById("sensorChart").getContext("2d");
  new Chart(ctx, {
    type: "line",
    data: {
      labels: ["09:00", "10:00", "11:00", "12:00", "13:00"],
      datasets: [{
        label: "Kelembapan & Kualitas Udara",
        data: data,
        borderColor: "#00aaff",
        backgroundColor: "rgba(0, 170, 255, 0.2)",
        fill: true,
        tension: 0.4
      }]
    },
    options: {
      responsive: true,
      scales: {
        y: { beginAtZero: true }
      }
    }
  });
}

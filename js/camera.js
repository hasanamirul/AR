document.getElementById("startAR").addEventListener("click", () => {
  const arSection = document.getElementById("ar-section");
  arSection.style.display = "block";
  if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    navigator.mediaDevices.getUserMedia({ video: true })
      .then(() => console.log("Kamera diaktifkan untuk AR"))
      .catch(err => alert("Gagal mengakses kamera: " + err));
  }
});

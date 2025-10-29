document.getElementById("btnCamera").addEventListener("click", () => {
  const arSection = document.getElementById("ar-section");
  arSection.classList.remove("hidden");
  
  // Minta izin kamera
  navigator.mediaDevices.getUserMedia({ video: true })
    .then((stream) => {
      console.log("Kamera aktif:", stream);
    })
    .catch((err) => {
      alert("Gagal mengakses kamera: " + err);
    });
});

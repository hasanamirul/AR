document.getElementById("btnCamera").addEventListener("click", async () => {
  const arSection = document.getElementById("ar-section");
  arSection.classList.remove("hidden");

  const videoContainer = document.getElementById("camera-container");
  videoContainer.innerHTML = ''; // bersihkan dulu
  const video = document.createElement("video");
  video.autoplay = true;
  video.playsInline = true;
  video.style.width = "100%";
  video.style.height = "100%";
  video.style.objectFit = "cover";
  videoContainer.appendChild(video);

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
    video.srcObject = stream;
  } catch (err) {
    alert("Gagal mengakses kamera: " + err);
    return;
  }

  const dummy = document.querySelector(".dummy-3d");
  dummy.style.display = "none";

  // Animasi scan 3 detik
  setTimeout(() => {
    dummy.style.display = "block";

    // Simulasi warna dummy sesuai AQI (opsional)
    const aqi = Math.floor(Math.random()*150);
    if(aqi <=50) dummy.style.background = "radial-gradient(circle,#00ff00,#007800)";
    else if(aqi <=100) dummy.style.background = "radial-gradient(circle,#ffff00,#ffaa00)";
    else dummy.style.background = "radial-gradient(circle,#ff0000,#770000)";

  }, 3000);
});

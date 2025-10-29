document.getElementById("btnCamera").addEventListener("click", async () => {
  const arSection = document.getElementById("ar-section");
  arSection.classList.remove("hidden");

  // Camera
  const videoContainer = document.getElementById("camera-container");
  videoContainer.innerHTML = '';
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

  const dummyObjects = [];
  for(let i=1;i<=6;i++){
    const dummy = document.getElementById(`dummy${i}`);
    dummyObjects.push(dummy);
    dummy.style.display = "none";

    // Ukuran random
    const size = 60 + Math.random() * 90; // 60-150px
    dummy.style.width = size + "px";
    dummy.style.height = size + "px";

    // Posisi random
    const left = 10 + Math.random() * 80; // 10%-90%
    const top = 10 + Math.random() * 80;  // 10%-90%
    dummy.style.left = left + "%";
    dummy.style.top = top + "%";

    // Animasi duration random
    dummy.style.animationDuration = `${4+Math.random()*4}s, ${3+Math.random()*3}s, ${4+Math.random()*3}s`;
  }

  // Scan 3 detik
  setTimeout(() => {
    dummyObjects.forEach(dummy => {
      dummy.style.display = "block";

      // Warna sesuai AQI random
      const aqi = Math.floor(Math.random()*150);
      if(aqi <=50) dummy.style.background = "radial-gradient(circle,#00ff00,#007800)";
      else if(aqi <=100) dummy.style.background = "radial-gradient(circle,#ffff00,#ffaa00)";
      else dummy.style.background = "radial-gradient(circle,#ff0000,#770000)";
    });
  }, 3000);
});

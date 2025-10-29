document.getElementById("btnCamera").addEventListener("click", async () => {
  const arSection = document.getElementById("ar-section");
  arSection.classList.remove("hidden");

  const videoContainer = document.getElementById("camera-container");
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
  }

  const dummy = document.querySelector(".dummy-3d");
  dummy.style.display = "none";

  setTimeout(() => { dummy.style.display = "block"; }, 3000); // dummy muncul setelah scan
});

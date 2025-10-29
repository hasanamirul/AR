let useFrontCamera = false;

const btnCamera = document.getElementById("btnCamera");
const arSection = document.getElementById("ar-section");
const scannerText = document.querySelector("#scanner p");
const modelViewer = document.querySelector("model-viewer");

btnCamera.addEventListener("click", async () => {
  arSection.classList.remove("hidden");
  scannerText.innerText = "🔍 Memindai lingkungan sekitar...";
  modelViewer.style.display = "none";

  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: useFrontCamera ? "user" : "environment" }
    });

    console.log("Kamera aktif:", stream);

    // Tambahkan tombol switch kamera jika belum ada
    if (!document.getElementById("btnSwitchCamera")) {
      const switchBtn = document.createElement("button");
      switchBtn.id = "btnSwitchCamera";
      switchBtn.innerText = "🔄 Switch Kamera";
      switchBtn.style.marginTop = "10px";
      switchBtn.onclick = () => {
        useFrontCamera = !useFrontCamera;
        btnCamera.click(); // restart kamera
      };
      arSection.appendChild(switchBtn);
    }

    // Animasi scan 3 detik
    setTimeout(() => {
      scannerText.innerText = "✅ Scan selesai!";
      modelViewer.style.display = "block";
    }, 3000);

  } catch (err) {
    alert("Gagal mengakses kamera: " + err);
  }
});

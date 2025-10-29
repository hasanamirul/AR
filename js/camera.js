let useFrontCamera = false;

const btnCamera = document.getElementById("btnCamera");
const arSection = document.getElementById("ar-section");

btnCamera.addEventListener("click", async () => {
  arSection.classList.remove("hidden");

  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: useFrontCamera ? "user" : "environment" }
    });

    console.log("Kamera aktif:", stream);

    // Tambahkan tombol switch kamera
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
  } catch (err) {
    alert("Gagal mengakses kamera: " + err);
  }
});

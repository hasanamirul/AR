document.getElementById("btnCamera").addEventListener("click", async () => {
  const arSection = document.getElementById("ar-section");
  arSection.classList.remove("hidden");

  // Camera setup
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

  // Dummy objects
  const dummyObjects = [];
  for(let i=1;i<=6;i++){
    const dummy = document.getElementById(`dummy${i}`);
    dummyObjects.push(dummy);

    // Random initial position
    dummy.style.left = `${10 + Math.random()*80}%`;
    dummy.style.top = `${10 + Math.random()*80}%`;
  }

  // Show dummy after scan animation
  setTimeout(()=>{
    dummyObjects.forEach(d => d.style.display="block");
  },3000);

  // Device orientation sway
  if(window.DeviceOrientationEvent){
    window.addEventListener("deviceorientation",(e)=>{
      const gamma = e.gamma || 0;
      const beta = e.beta || 0;
      dummyObjects.forEach(d=>{
        d.style.transform = `translate(-50%,-50%) translateX(${gamma/3}px) translateY(${beta/4}px)`;
      });
    });
  }

  // Tooltip on click
  const tooltip = document.getElementById("dummy-tooltip");
  dummyObjects.forEach(d => {
    d.addEventListener("click",(e)=>{
      tooltip.innerText = d.getAttribute("data-sensor");
      tooltip.style.left = e.clientX + "px";
      tooltip.style.top = e.clientY - 40 + "px";
      tooltip.classList.remove("hidden");
      setTimeout(()=>tooltip.classList.add("hidden"),3000);
    });
  });

  // Floating + rotate animations handled via CSS keyframes
});

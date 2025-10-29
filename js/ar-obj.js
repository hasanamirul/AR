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

  // Three.js setup
  const container = document.createElement("div");
  container.style.width = "100%";
  container.style.height = "100%";
  container.style.position = "absolute";
  container.style.top = 0;
  container.style.left = 0;
  container.style.pointerEvents = "none";
  arSection.appendChild(container);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 0.1, 1000);
  camera.position.z = 2;

  const renderer = new THREE.WebGLRenderer({ alpha:true, antialias:true });
  renderer.setSize(container.clientWidth, container.clientHeight);
  container.appendChild(renderer.domElement);

  // Lights
  const dirLight = new THREE.DirectionalLight(0xffffff, 1);
  dirLight.position.set(1,1,1);
  scene.add(dirLight);
  const ambient = new THREE.AmbientLight(0xffffff, 0.5);
  scene.add(ambient);

  // Load OBJ model
  const loader = new THREE.OBJLoader();
  loader.load('assets/models/cloud.obj', (obj)=>{
    obj.scale.set(0.5,0.5,0.5);
    obj.position.set(0,0,0);
    obj.rotation.y = Math.PI/4;
    scene.add(obj);

    // Dummy animation: rotate + float
    const animate = function(){
      requestAnimationFrame(animate);
      obj.rotation.y += 0.01;
      obj.position.y = 0.2 * Math.sin(Date.now()*0.002);
      renderer.render(scene,camera);
    };
    animate();
  });

  // Floating dummy circles overlay (optional)
  const dummyObjects = [];
  for(let i=1;i<=6;i++){
    const dummy = document.getElementById(`dummy${i}`);
    dummyObjects.push(dummy);
    dummy.style.display = "none";

    // Random size & position
    const size = 60 + Math.random()*90;
    dummy.style.width = size+"px";
    dummy.style.height = size+"px";
    const left = 10 + Math.random()*80;
    const top = 10 + Math.random()*80;
    dummy.style.left = left+"%";
    dummy.style.top = top+"%";

    dummy.style.animationDuration = `${4+Math.random()*4}s, ${3+Math.random()*3}s, ${4+Math.random()*3}s, ${5+Math.random()*4}s`;
  }

  // Show dummy after 3s scan
  setTimeout(()=>{
    dummyObjects.forEach(dummy=>{
      dummy.style.display="block";
    });
  },3000);

  // Device orientation → sway dummy
  if(window.DeviceOrientationEvent){
    window.addEventListener("deviceorientation",(event)=>{
      const gamma = event.gamma || 0;
      const beta = event.beta || 0;
      dummyObjects.forEach(dummy=>{
        dummy.style.transform = `translate(-50%,-50%) translateX(${gamma/3}px) translateY(${beta/4}px)`;
      });
    });
  }

  // Responsive renderer
  window.addEventListener('resize', ()=>{
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(container.clientWidth, container.clientHeight);
  });
});

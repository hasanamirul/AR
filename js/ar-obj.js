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
} catch(err) {
  alert("Gagal mengakses kamera: " + err);
  return;
}


// Three.js setup
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, videoContainer.clientWidth/videoContainer.clientHeight, 0.1, 1000);
camera.position.z = 2;

const renderer = new THREE.WebGLRenderer({ alpha:true, antialias:true });
renderer.setSize(videoContainer.clientWidth, videoContainer.clientHeight);
renderer.domElement.style.position = "absolute";
renderer.domElement.style.top = 0;
renderer.domElement.style.left = 0;
renderer.domElement.style.pointerEvents = "none";
videoContainer.appendChild(renderer.domElement);

// Lights
const light = new THREE.DirectionalLight(0xffffff, 1);
light.position.set(1,1,1);
scene.add(light);
scene.add(new THREE.AmbientLight(0xffffff,0.5));


const loader = new THREE.OBJLoader();
loader.load('assets/models/cloud.obj', function(object){
    object.scale.set(0.5,0.5,0.5);   // sesuaikan ukuran
    object.position.set(0,0,0);       // posisi di tengah AR
    scene.add(object);

    // animasi dummy
    function animate(){
        requestAnimationFrame(animate);
        object.rotation.y += 0.01;              // rotate
        object.position.y = 0.2*Math.sin(Date.now()*0.002); // float
        renderer.render(scene,camera);
    }
    animate();
});






window.addEventListener('resize', () => {
  camera.aspect = videoContainer.clientWidth / videoContainer.clientHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(videoContainer.clientWidth, videoContainer.clientHeight);
});

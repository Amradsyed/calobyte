import * as THREE from "https://unpkg.com/three@0.160.0/build/three.module.js";

const canvas = document.getElementById("calobyte-scene");

const colors = {
  panel: 0x102033,
  cyan: 0x43c6d9,
  green: 0x42d392,
  orange: 0xf0a14a,
  white: 0xedf6fb
};

let scene;
let camera;
let renderer;
let root;

function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}

function makeTexture(title, value, caption, accent) {
  const c = document.createElement("canvas");
  c.width = 720;
  c.height = 340;

  const ctx = c.getContext("2d");
  ctx.fillStyle = "rgba(16,32,51,.95)";
  roundRect(ctx, 0, 0, c.width, c.height, 34);
  ctx.fill();

  ctx.strokeStyle = "rgba(219,231,242,.22)";
  ctx.lineWidth = 3;
  roundRect(ctx, 2, 2, c.width - 4, c.height - 4, 34);
  ctx.stroke();

  ctx.fillStyle = "#9eb0c0";
  ctx.font = "600 32px Inter, Arial";
  ctx.fillText(title, 38, 68);

  ctx.fillStyle = accent;
  ctx.font = "800 58px Inter, Arial";
  ctx.fillText(value, 38, 150);

  ctx.fillStyle = "#edf6fb";
  ctx.font = "600 26px Inter, Arial";
  ctx.fillText(caption, 38, 220);

  const texture = new THREE.CanvasTexture(c);
  texture.anisotropy = 8;
  return texture;
}

function makePanel(texture, w, h) {
  return new THREE.Mesh(
    new THREE.PlaneGeometry(w, h),
    new THREE.MeshStandardMaterial({
      map: texture,
      transparent: true,
      roughness: 0.48,
      metalness: 0.08,
      side: THREE.DoubleSide
    })
  );
}

function makeBox(w, h, d, color, opacity = 1) {
  return new THREE.Mesh(
    new THREE.BoxGeometry(w, h, d),
    new THREE.MeshStandardMaterial({
      color,
      roughness: 0.46,
      metalness: 0.12,
      transparent: opacity < 1,
      opacity
    })
  );
}

function makeRing(radius, tube, color) {
  return new THREE.Mesh(
    new THREE.TorusGeometry(radius, tube, 28, 96),
    new THREE.MeshStandardMaterial({
      color,
      emissive: color,
      emissiveIntensity: 0.13,
      roughness: 0.35,
      metalness: 0.2
    })
  );
}

function buildScene() {
  scene = new THREE.Scene();

  camera = new THREE.PerspectiveCamera(
    36,
    canvas.clientWidth / canvas.clientHeight,
    0.1,
    100
  );
  camera.position.set(0.8, 2.1, 9.2);

  renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: true,
    alpha: true
  });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(canvas.clientWidth, canvas.clientHeight, false);
  renderer.outputColorSpace = THREE.SRGBColorSpace;

  scene.add(new THREE.AmbientLight(0xffffff, 1.6));

  const key = new THREE.DirectionalLight(0xffffff, 2.2);
  key.position.set(4, 6, 5);
  scene.add(key);

  const rim = new THREE.PointLight(colors.cyan, 26, 16);
  rim.position.set(-3.8, 2.6, 3.6);
  scene.add(rim);

  root = new THREE.Group();
  root.rotation.set(-0.08, -0.33, 0.02);
  scene.add(root);

  const backplate = makeBox(5.7, 3.65, 0.12, colors.panel, 0.86);
  backplate.position.set(0, 0, -0.08);
  root.add(backplate);

  const mainPanel = makePanel(
    makeTexture("Daily nutrition", "1,690 kcal left", "Meal plan, hydration, and AI guidance.", "#43c6d9"),
    3.6,
    1.7
  );
  mainPanel.position.set(-0.55, 0.63, 0.04);
  root.add(mainPanel);

  const coachPanel = makePanel(
    makeTexture("AI Coach", "Protein first", "Short guidance from daily progress.", "#42d392"),
    2.75,
    1.3
  );
  coachPanel.position.set(1.1, -1.02, 0.08);
  root.add(coachPanel);

  const mealPanel = makePanel(
    makeTexture("Weekly Plan", "7 days", "Breakfast, lunch, dinner, and macros.", "#f0a14a"),
    2.35,
    1.18
  );
  mealPanel.position.set(-1.9, -1.08, 0.1);
  root.add(mealPanel);

  const ringGroup = new THREE.Group();
  ringGroup.position.set(2.04, 0.78, 0.38);
  ringGroup.add(makeRing(0.52, 0.025, colors.green));
  ringGroup.add(makeRing(0.72, 0.026, colors.cyan));
  ringGroup.add(makeRing(0.91, 0.024, colors.orange));
  root.add(ringGroup);

  const droplet = new THREE.Mesh(
    new THREE.SphereGeometry(0.22, 32, 32),
    new THREE.MeshStandardMaterial({
      color: colors.cyan,
      emissive: colors.cyan,
      emissiveIntensity: 0.12,
      roughness: 0.22,
      metalness: 0.25
    })
  );
  droplet.scale.set(0.78, 1.24, 0.78);
  droplet.position.set(2.53, -0.16, 0.5);
  root.add(droplet);

  const bowl = makeBox(0.96, 0.25, 0.48, 0xf3f6f2, 0.95);
  bowl.position.set(-2.62, 0.28, 0.48);
  bowl.rotation.set(0.28, -0.35, 0.08);
  root.add(bowl);

  const foodColors = [colors.green, colors.orange, colors.cyan, 0xf6d27b];
  for (let i = 0; i < 8; i++) {
    const food = new THREE.Mesh(
      new THREE.SphereGeometry(0.07 + (i % 2) * 0.02, 18, 18),
      new THREE.MeshStandardMaterial({
        color: foodColors[i % foodColors.length],
        roughness: 0.4
      })
    );
    food.position.set(
      -2.94 + (i % 4) * 0.18,
      0.48 + Math.floor(i / 4) * 0.1,
      0.55 + (i % 3) * 0.05
    );
    root.add(food);
  }
}

function animate(time = 0) {
  const t = time * 0.001;

  if (root) {
    root.rotation.y = -0.33 + Math.sin(t * 0.38) * 0.035;
    root.rotation.x = -0.08 + Math.cos(t * 0.3) * 0.018;
    root.position.y = Math.sin(t * 0.75) * 0.08;

    root.children.forEach((child, i) => {
      if (child.geometry && child.geometry.type === "TorusGeometry") {
        child.rotation.z += 0.004 + i * 0.0008;
      }
    });
  }

  renderer.render(scene, camera);
  requestAnimationFrame(animate);
}

function resize() {
  if (!renderer || !camera) return;

  const width = canvas.clientWidth;
  const height = canvas.clientHeight;

  renderer.setSize(width, height, false);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
}

try {
  buildScene();
  resize();
  window.addEventListener("resize", resize);
  animate();
} catch (error) {
  console.error("CaloByte 3D scene failed:", error);
  document.body.classList.add("scene-failed");
}
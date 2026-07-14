/* Real-time 3D house scene — drag to orbit, glowing particle streams show
   live power flow. Loaded dynamically by app.js; the bare specifier 'three'
   resolves via the importmap in index.html. */

import * as THREE from "three";
import { OrbitControls } from "./vendor/OrbitControls.js";

const ENTITY = {
  solar:   { color: 0xffb020, label: "SOLAR" },
  battery: { color: 0x1fd598, label: "BATTERY" },
  home:    { color: 0xa89bff, label: "LOAD" },
  grid:    { color: 0x4da3ff, label: "GRID" },
};

let renderer, scene, camera, controls;
let container, chipEls = {}, chipAnchors = {};
let flows = {};
let windowsMat, panelsMat, battLedMat, porchLight;
let active = true;

/* ---------- small helpers ---------- */

function glowTexture() {
  const c = document.createElement("canvas");
  c.width = c.height = 64;
  const g = c.getContext("2d");
  const grad = g.createRadialGradient(32, 32, 0, 32, 32, 32);
  grad.addColorStop(0, "rgba(255,255,255,1)");
  grad.addColorStop(0.4, "rgba(255,255,255,0.5)");
  grad.addColorStop(1, "rgba(255,255,255,0)");
  g.fillStyle = grad;
  g.fillRect(0, 0, 64, 64);
  return new THREE.CanvasTexture(c);
}
const GLOW_TEX = glowTexture();

function box(w, h, d, color, opts = {}) {
  const m = new THREE.Mesh(
    new THREE.BoxGeometry(w, h, d),
    new THREE.MeshStandardMaterial({
      color,
      roughness: opts.rough ?? 0.85,
      metalness: opts.metal ?? 0.1,
      emissive: opts.emissive ?? 0x000000,
      emissiveIntensity: opts.ei ?? 0,
    })
  );
  if (opts.pos) m.position.set(...opts.pos);
  return m;
}

/* ---------- environment ---------- */

function buildEnvironment() {
  scene.background = new THREE.Color(0x0e0d1d);
  scene.fog = new THREE.Fog(0x0e0d1d, 34, 70);

  scene.add(new THREE.AmbientLight(0x5a64a8, 1.15));
  const moon = new THREE.DirectionalLight(0x99aaee, 2.4);
  moon.position.set(-8, 14, -6);
  scene.add(moon);
  const fill = new THREE.DirectionalLight(0x445599, 0.9);
  fill.position.set(10, 6, 10);
  scene.add(fill);

  // moon disc
  const moonSprite = new THREE.Sprite(new THREE.SpriteMaterial({
    map: GLOW_TEX, color: 0xdfe2ff, blending: THREE.AdditiveBlending,
    depthWrite: false, opacity: 0.95,
  }));
  moonSprite.position.set(-22, 24, -30);
  moonSprite.scale.setScalar(7);
  scene.add(moonSprite);

  // stars
  const pts = [];
  for (let i = 0; i < 420; i++) {
    const a = Math.random() * Math.PI * 2, e = Math.random() * 0.9 + 0.08, r = 55;
    pts.push(
      r * Math.cos(e) * Math.cos(a),
      r * Math.sin(e),
      r * Math.cos(e) * Math.sin(a),
    );
  }
  const starGeo = new THREE.BufferGeometry();
  starGeo.setAttribute("position", new THREE.Float32BufferAttribute(pts, 3));
  scene.add(new THREE.Points(starGeo, new THREE.PointsMaterial({
    color: 0xc9c4ff, size: 0.14, sizeAttenuation: true,
    transparent: true, opacity: 0.75, depthWrite: false,
  })));

  // ground + lawn + driveway
  const ground = new THREE.Mesh(
    new THREE.CircleGeometry(30, 56),
    new THREE.MeshStandardMaterial({ color: 0x191833, roughness: 1 })
  );
  ground.rotation.x = -Math.PI / 2;
  scene.add(ground);
  const lawn = new THREE.Mesh(
    new THREE.CircleGeometry(12, 48),
    new THREE.MeshStandardMaterial({ color: 0x1d2743, roughness: 1 })
  );
  lawn.rotation.x = -Math.PI / 2;
  lawn.position.y = 0.01;
  scene.add(lawn);
  const drive = new THREE.Mesh(
    new THREE.PlaneGeometry(2.8, 9),
    new THREE.MeshStandardMaterial({ color: 0x232238, roughness: 0.9 })
  );
  drive.rotation.x = -Math.PI / 2;
  drive.position.set(-1.6, 0.02, 7.4);
  scene.add(drive);

  // a couple of dark garden trees for depth
  for (const [x, z, s] of [[-9, -6, 1.3], [10, -5, 1.5], [11, 8, 1.1]]) {
    const trunk = box(0.18 * s, 0.9 * s, 0.18 * s, 0x241f33, { pos: [x, 0.45 * s, z] });
    const crown = new THREE.Mesh(
      new THREE.ConeGeometry(1.05 * s, 2.6 * s, 7),
      new THREE.MeshStandardMaterial({ color: 0x233152, roughness: 1 })
    );
    crown.position.set(x, 2.1 * s, z);
    scene.add(trunk, crown);
  }
}

/* ---------- house ---------- */

function buildHouse() {
  // walls (8 wide × 3 high × 6 deep, front faces +z)
  scene.add(box(8, 3, 6, 0x4a4a78, { pos: [0, 1.5, 0] }));
  // skillion roof slab + trim
  scene.add(box(8.7, 0.28, 6.7, 0x30304e, { pos: [0, 3.22, 0] }));
  scene.add(box(8.8, 0.06, 6.8, 0x62629a, { pos: [0, 3.39, 0] }));

  // solar array 4 × 3
  panelsMat = new THREE.MeshStandardMaterial({
    color: 0x10315e, roughness: 0.3, metalness: 0.45,
    emissive: 0x1a5dbf, emissiveIntensity: 0.1,
  });
  const cell = new THREE.BoxGeometry(1.55, 0.07, 1.35);
  for (let r = 0; r < 3; r++) {
    for (let c = 0; c < 4; c++) {
      const p = new THREE.Mesh(cell, panelsMat);
      p.position.set(-2.6 + c * 1.74, 3.46, -1.6 + r * 1.6);
      scene.add(p);
    }
  }

  // windows — emissive warm glass, brightness follows house load
  windowsMat = new THREE.MeshStandardMaterial({
    color: 0x2a1f12, emissive: 0xff9a3d, emissiveIntensity: 0.35,
    roughness: 0.4,
  });
  const winGeo = new THREE.PlaneGeometry(1.15, 0.95);
  for (const [x, y, z, ry] of [
    [-2.3, 1.75, 3.01, 0], [-0.6, 1.75, 3.01, 0],   // front
    [4.01, 1.75, -0.6, Math.PI / 2],                // right side
    [-4.01, 1.75, 0.4, -Math.PI / 2],               // left side
    [-1.6, 1.75, -3.01, Math.PI], [1.4, 1.75, -3.01, Math.PI],  // back
  ]) {
    const w = new THREE.Mesh(winGeo, windowsMat);
    w.position.set(x, y, z);
    w.rotation.y = ry;
    scene.add(w);
  }
  // door
  const door = new THREE.Mesh(
    new THREE.PlaneGeometry(1.0, 2.1),
    new THREE.MeshStandardMaterial({ color: 0x191826, roughness: 0.7 })
  );
  door.position.set(1.3, 1.06, 3.01);
  scene.add(door);
  porchLight = new THREE.PointLight(0xffa050, 42, 10, 2);
  porchLight.position.set(1.3, 2.5, 3.8);
  scene.add(porchLight);

  // inverter on the front wall (flow hub)
  scene.add(box(0.55, 0.75, 0.14, 0x20203a, { pos: [2.65, 1.35, 3.06] }));
  scene.add(box(0.4, 0.06, 0.04, 0x3987e5, {
    pos: [2.65, 1.15, 3.14], emissive: 0x3987e5, ei: 1.4,
  }));

  // battery cabinet
  scene.add(box(1.0, 1.6, 0.7, 0x3a3a66, { pos: [5.7, 0.8, 1.2] }));
  battLedMat = new THREE.MeshStandardMaterial({
    color: 0x1fd598, emissive: 0x1fd598, emissiveIntensity: 1.6,
  });
  const led = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.05, 0.04), battLedMat);
  led.position.set(5.7, 1.35, 1.57);
  scene.add(led);

  // power pole + sagging service wire
  scene.add(new THREE.Mesh(
    new THREE.CylinderGeometry(0.09, 0.12, 5.4, 8),
    new THREE.MeshStandardMaterial({ color: 0x2e2b45, roughness: 1 })
  ).translateX(-10.5).translateY(2.7).translateZ(4));
  scene.add(box(1.5, 0.09, 0.09, 0x2e2b45, { pos: [-10.5, 4.9, 4] }));
  const wireCurve = new THREE.CatmullRomCurve3([
    new THREE.Vector3(-10.5, 5.1, 4),
    new THREE.Vector3(-7.4, 3.6, 3.6),
    new THREE.Vector3(-4.1, 3.2, 3.0),
  ]);
  scene.add(new THREE.Mesh(
    new THREE.TubeGeometry(wireCurve, 24, 0.016, 5),
    new THREE.MeshBasicMaterial({ color: 0x3c3a5c })
  ));

  // garden bollard lights
  for (const [x, z] of [[-3.2, 5.6], [0.4, 5.9], [3.8, 5.2], [5.9, 3.6]]) {
    scene.add(box(0.07, 0.45, 0.07, 0x2a2740, {
      pos: [x, 0.22, z], emissive: 0xffaa55, ei: 0.9,
    }));
  }
}

/* ---------- power flows (particle streams) ---------- */

function makeFlow(key, points) {
  const curve = new THREE.CatmullRomCurve3(points.map((p) => new THREE.Vector3(...p)), false, "centripetal");
  const mat = new THREE.SpriteMaterial({
    map: GLOW_TEX, color: ENTITY[key].color,
    blending: THREE.AdditiveBlending, depthWrite: false, transparent: true,
  });
  const sprites = [];
  for (let i = 0; i < 18; i++) {
    const s = new THREE.Sprite(mat.clone());
    s.scale.setScalar(0.17);
    s.userData.t = i / 18;
    s.visible = false;
    scene.add(s);
    sprites.push(s);
  }
  // faint conduit line so the route reads even when idle
  const tube = new THREE.Mesh(
    new THREE.TubeGeometry(curve, 32, 0.012, 5),
    new THREE.MeshBasicMaterial({
      color: ENTITY[key].color, transparent: true, opacity: 0.10,
    })
  );
  scene.add(tube);
  flows[key] = { curve, sprites, tube, watts: 0, reverse: false };
}

function buildFlows() {
  makeFlow("grid", [
    [-10.5, 5.1, 4], [-7.4, 3.6, 3.6], [-4.1, 3.2, 3.0],
    [-1.5, 2.4, 3.35], [2.65, 1.5, 3.3],
  ]);
  makeFlow("solar", [
    [0.6, 3.75, 0.2], [2.65, 3.55, 2.7], [2.65, 2.4, 3.3], [2.65, 1.8, 3.3],
  ]);
  makeFlow("battery", [
    [5.7, 1.75, 1.25], [4.9, 1.7, 2.7], [3.1, 1.45, 3.3],
  ]);
  makeFlow("home", [
    [2.65, 1.1, 3.3], [2.1, 0.65, 3.7], [1.3, 0.35, 3.4],
  ]);
}

function animateFlows(dt) {
  for (const f of Object.values(flows)) {
    const on = Math.abs(f.watts) > 40;
    f.tube.material.opacity = on ? 0.28 : 0.10;
    const speed = 0.10 + Math.min(0.5, Math.abs(f.watts) / 9000);
    const scale = 0.13 + Math.min(0.12, Math.abs(f.watts) / 25000);
    for (const s of f.sprites) {
      if (!on) { s.visible = false; continue; }
      s.visible = true;
      s.userData.t = (s.userData.t + dt * speed) % 1;
      const t = f.reverse ? 1 - s.userData.t : s.userData.t;
      f.curve.getPointAt(t, s.position);
      s.scale.setScalar(scale);
    }
  }
}

/* ---------- data chips (HTML overlay) ---------- */

function buildChips() {
  chipAnchors = {
    solar:   new THREE.Vector3(0, 4.3, -0.2),
    grid:    new THREE.Vector3(-10.5, 5.7, 4),
    battery: new THREE.Vector3(5.7, 2.4, 1.2),
    home:    new THREE.Vector3(1.3, 0.15, 4.6),
  };
  for (const key of Object.keys(chipAnchors)) {
    const div = document.createElement("div");
    div.className = "chip3d";
    div.innerHTML = `<i style="background:#${ENTITY[key].color.toString(16).padStart(6, "0")}"></i>
      <div><b class="cv">—</b><span class="cs">${ENTITY[key].label}</span></div>`;
    container.appendChild(div);
    chipEls[key] = div;
  }
}

function positionChips() {
  const w = container.clientWidth, h = container.clientHeight;
  const v = new THREE.Vector3();
  for (const [key, anchor] of Object.entries(chipAnchors)) {
    v.copy(anchor).project(camera);
    const el = chipEls[key];
    if (v.z > 1) { el.style.display = "none"; continue; }
    el.style.display = "flex";
    el.style.left = `${((v.x + 1) / 2) * w}px`;
    el.style.top = `${((1 - v.y) / 2) * h}px`;
  }
}

/* ---------- public API ---------- */

export function isSupported() {
  try {
    const c = document.createElement("canvas");
    return !!(window.WebGLRenderingContext &&
      (c.getContext("webgl2") || c.getContext("webgl")));
  } catch (e) { return false; }
}

export function init(el) {
  container = el;
  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(el.clientWidth, el.clientHeight);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.35;
  el.appendChild(renderer.domElement);

  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(42, el.clientWidth / el.clientHeight, 0.1, 200);
  camera.position.set(11.5, 6.8, 12.5);

  controls = new OrbitControls(camera, renderer.domElement);
  controls.target.set(0, 1.6, 0.8);
  controls.enableDamping = true;
  controls.dampingFactor = 0.06;
  controls.enablePan = false;
  controls.minDistance = 8;
  controls.maxDistance = 34;
  controls.maxPolarAngle = 1.42;
  controls.autoRotate = true;
  controls.autoRotateSpeed = 0.6;
  controls.addEventListener("start", () => { controls.autoRotate = false; });

  buildEnvironment();
  buildHouse();
  buildFlows();
  buildChips();

  new ResizeObserver(() => {
    const w = el.clientWidth, h = el.clientHeight;
    if (!w || !h) return;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
  }).observe(el);

  const clock = new THREE.Clock();
  (function loop() {
    requestAnimationFrame(loop);
    if (!active || document.hidden) return;
    const dt = Math.min(clock.getDelta(), 0.1);
    controls.update();
    animateFlows(dt);
    renderer.render(scene, camera);
    positionChips();
  })();
}

const fmt = (w) => (Math.abs(w) >= 1000 ? `${(w / 1000).toFixed(2)} kW` : `${Math.round(w)} W`);

export function update(s) {
  flows.solar.watts = s.ppv;
  flows.battery.watts = s.pbat;
  flows.battery.reverse = s.pbat < 0;      // charging: house → battery
  flows.home.watts = s.pload;
  flows.grid.watts = s.pgrid;
  flows.grid.reverse = s.pgrid < 0;        // exporting: house → pole

  chipEls.solar.querySelector(".cv").textContent = fmt(s.ppv);
  chipEls.home.querySelector(".cv").textContent = fmt(s.pload);
  chipEls.grid.querySelector(".cv").textContent =
    `${fmt(Math.abs(s.pgrid))}${s.pgrid > 40 ? " in" : s.pgrid < -40 ? " out" : ""}`;
  chipEls.battery.querySelector(".cv").textContent =
    `${s.soc.toFixed(0)}% ${s.pbat < -40 ? "▲" : s.pbat > 40 ? "▼" : ""}`;

  windowsMat.emissiveIntensity = 0.25 + Math.min(1.5, s.pload / 2200);
  porchLight.intensity = 25 + Math.min(50, s.pload / 80);
  panelsMat.emissiveIntensity = s.ppv > 20 ? 0.4 : 0.08;
  battLedMat.emissive.setHex(
    s.pbat < -40 ? 0x1fd598 : s.pbat > 40 ? 0xffb020 : 0x555577);
  battLedMat.color.setHex(battLedMat.emissive.getHex());
}

export function setActive(v) { active = v; }

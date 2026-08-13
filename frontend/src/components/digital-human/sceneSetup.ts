/** Three.js 场景/相机/灯光 初始化 */

import * as THREE from 'three';

export interface SceneSetup {
  scene: THREE.Scene;
  camera: THREE.PerspectiveCamera;
  renderer: THREE.WebGLRenderer;
}

export function createScene(canvas: HTMLCanvasElement, width: number, height: number): SceneSetup {
  // ---- Scene ----
  const scene = new THREE.Scene();

  // ---- Camera ----
  // Bust (head-and-shoulders) framing. The model is scaled to 2.2m tall with feet at y=0,
  // so the head sits around y≈2.0. Frame the upper body: camera at head height,
  // closer in, looking straight at the head/upper-chest center.
  const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
  camera.position.set(0, 1.65, 1.4);
  camera.lookAt(0, 1.65, 0);

  // ---- Renderer ----
  const renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: true,
    alpha: true,
  });
  renderer.setSize(width, height, false); // false = use CSS pixels, not device pixels
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.2;

  // ---- Lighting ----
  // Ambient — base fill
  const ambient = new THREE.AmbientLight(0xffffff, 0.6);
  scene.add(ambient);

  // Key light — from front-right
  const keyLight = new THREE.DirectionalLight(0xffffff, 1.5);
  keyLight.position.set(1.5, 1.8, 3);
  scene.add(keyLight);

  // Rim light — from behind
  const rimLight = new THREE.DirectionalLight(0x8899cc, 0.8);
  rimLight.position.set(-0.5, 1.0, -2);
  scene.add(rimLight);

  // Fill light — from left
  const fillLight = new THREE.DirectionalLight(0xccddff, 0.5);
  fillLight.position.set(-1.5, 0.5, 2);
  scene.add(fillLight);

  return { scene, camera, renderer };
}

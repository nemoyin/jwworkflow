/** GLTFLoader 封装 — 加载 ReadyPlayerMe GLB 模型，提取 morph targets */

import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

export interface LoadedModel {
  /** The root Group from the GLTF */
  group: THREE.Group;
  /** First skinned mesh with morph targets (usually the face/head) */
  mesh: THREE.SkinnedMesh | null;
  /** ALL skinned meshes carrying morph targets (eyes, head, teeth) — driven together */
  morphMeshes: THREE.SkinnedMesh[];
  /** Map of morph target name → index */
  morphTargets: Map<string, number>;
  /** Bounding box for sizing */
  boundingBox: THREE.Box3;
}

// Default avatar — bundled locally (public/avatar.glb) to avoid external CDN dependency.
// The model is a ReadyPlayerMe avatar with 52 ARKit morph targets (jawOpen, eyeBlink*, mouth*, brow*…).
const DEFAULT_AVATAR_URL = '/avatar.glb';

// Canonical ARKit 52 blendshape names, in order. ReadyPlayerMe GLBs carry 52 morph
// targets on their facial meshes but ship NO `extras.targetNames`, so GLTFLoader
// leaves `morphTargetDictionary` undefined. We map target indices → names using
// this standard order so animation code can address morphs by name.
const ARKIT_MORPH_TARGETS = [
  'browDownLeft', 'browDownRight', 'browInnerUp', 'browOuterUpLeft', 'browOuterUpRight',
  'cheekPuff', 'cheekSquintLeft', 'cheekSquintRight',
  'eyeBlinkLeft', 'eyeBlinkRight', 'eyeLookDownLeft', 'eyeLookDownRight', 'eyeLookInLeft', 'eyeLookInRight', 'eyeLookOutLeft', 'eyeLookOutRight', 'eyeLookUpLeft', 'eyeLookUpRight', 'eyeSquintLeft', 'eyeSquintRight', 'eyeWideLeft', 'eyeWideRight',
  'jawForward', 'jawLeft', 'jawOpen', 'jawRight',
  'mouthClose', 'mouthDimpleLeft', 'mouthDimpleRight', 'mouthFrownLeft', 'mouthFrownRight', 'mouthFunnel', 'mouthLeft', 'mouthLowerDownLeft', 'mouthLowerDownRight', 'mouthPressLeft', 'mouthPressRight', 'mouthPucker', 'mouthRight', 'mouthRollLower', 'mouthRollUpper', 'mouthShrugLower', 'mouthShrugUpper', 'mouthSmileLeft', 'mouthSmileRight', 'mouthStretchLeft', 'mouthStretchRight', 'mouthUpperUpLeft', 'mouthUpperUpRight',
  'noseSneerLeft', 'noseSneerRight', 'tongueOut',
];

const loader = new GLTFLoader();

export function loadModel(url?: string): Promise<LoadedModel> {
  const modelUrl = url || DEFAULT_AVATAR_URL;

  return new Promise((resolve, reject) => {
    loader.load(
      modelUrl,
      (gltf) => {
        const group = gltf.scene;

        // Collect every skinned mesh that carries morph targets (ReadyPlayerMe puts
        // the same 52 blendshapes on EyeLeft/EyeRight/Head/Teeth — all must move together).
        let mesh: THREE.SkinnedMesh | null = null;
        const morphMeshes: THREE.SkinnedMesh[] = [];
        const morphTargets = new Map<string, number>();

        group.traverse((child) => {
          if (!(child instanceof THREE.SkinnedMesh)) return;
          const infl = child.morphTargetInfluences;
          if (!infl || infl.length === 0) return;

          const dict = child.morphTargetDictionary;
          const dictKeys = dict ? Object.keys(dict) : [];

          if (dictKeys.length > 0) {
            // Names supplied by the file — use them directly.
            dictKeys.forEach((name) => morphTargets.set(name, dict![name] as number));
          } else if (infl.length === ARKIT_MORPH_TARGETS.length && morphTargets.size === 0) {
            // No targetNames — assume canonical ARKit order.
            ARKIT_MORPH_TARGETS.forEach((name, i) => morphTargets.set(name, i));
          }

          // Defensive: guarantee morphing is enabled on the material so target
          // weight changes actually render (GLTFLoader normally sets this).
          const mats = Array.isArray(child.material) ? child.material : [child.material];
          mats.forEach((m) => {
            if (m) (m as THREE.Material & { morphTargets?: boolean }).morphTargets = true;
          });

          morphMeshes.push(child);
          if (!mesh) mesh = child;
        });

        // Compute bounding box for sizing
        const boundingBox = new THREE.Box3().setFromObject(group);

        // Center and scale
        const size = boundingBox.getSize(new THREE.Vector3());
        const maxDim = Math.max(size.x, size.y, size.z);
        const targetHeight = 2.2; // meters — full body ~head room above
        const scale = targetHeight / maxDim;
        group.scale.setScalar(scale);

        // Re-compute after scaling
        boundingBox.setFromObject(group);

        // Center horizontally
        const center = boundingBox.getCenter(new THREE.Vector3());
        group.position.set(-center.x, -boundingBox.min.y, -center.z);

        resolve({ group, mesh, morphMeshes, morphTargets, boundingBox });
      },
      (progress) => {
        // Loading progress — could be wired to a progress bar
        if (progress.total > 0) {
          const pct = Math.round((progress.loaded / progress.total) * 100);
          console.debug(`[ModelLoader] ${pct}% loaded`);
        }
      },
      (error) => {
        reject(new Error(`Failed to load model: ${(error as any)?.message || error}`));
      },
    );
  });
}

/**
 * Create a fallback sphere avatar for when the model hasn't loaded yet.
 */
export function createFallbackMesh(): THREE.Mesh {
  const geometry = new THREE.SphereGeometry(0.5, 64, 64);
  const material = new THREE.MeshStandardMaterial({
    color: 0x4a6fa5,
    roughness: 0.4,
    metalness: 0.1,
  });
  const mesh = new THREE.Mesh(geometry, material);
  mesh.position.set(0, 1.65, 0); // head height, matching default camera framing
  mesh.name = 'fallback-avatar';
  return mesh;
}

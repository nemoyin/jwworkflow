/** React Hook — Three.js 数字人生命周期管理 */

import { useRef, useEffect, useCallback, useState } from 'react';
import * as THREE from 'three';
import { createScene } from './sceneSetup';
import { loadModel, createFallbackMesh } from './modelLoader';
import type { LoadedModel } from './modelLoader';
import type { TTSBoundaryEvent } from './useSpeechSynthesis';

interface UseDigitalHumanOptions {
  /** Canvas element (ref) */
  canvasRef: React.RefObject<HTMLCanvasElement | null>;
  /** Optional custom model URL */
  modelUrl?: string;
}

interface UseDigitalHumanReturn {
  /** Whether the 3D scene is ready */
  ready: boolean;
  /** Whether the model is loaded */
  modelLoaded: boolean;
  /** Loading progress (0-1) */
  loadProgress: number;
  /** Map of morph target names → indices */
  morphTargets: Map<string, number>;
  /** Set a specific morph target weight */
  setMorphWeight: (name: string, value: number) => void;
  /** Smoothly animate a morph target to a target value */
  animateMorph: (name: string, target: number, duration: number) => void;
  /** Handle TTS boundary event for lip-sync */
  handleBoundary: (e: TTSBoundaryEvent) => void;
  /** Apply an expression preset */
  setExpression: (expression: string, intensity?: number) => void;
}

// Idle animation parameters
const IDLE_BREATH_AMPLITUDE = 0.025; // visible chest rise/fall (m)
const IDLE_BREATH_FREQUENCY = 0.8;
const IDLE_SWAY_AMPLITUDE = 0.04; // visible head sway (rad)
const IDLE_SWAY_FREQUENCY = 0.3;

export function useDigitalHuman({ canvasRef, modelUrl }: UseDigitalHumanOptions): UseDigitalHumanReturn {
  const [ready, setReady] = useState(false);
  const [modelLoaded, setModelLoaded] = useState(false);
  const [loadProgress, setLoadProgress] = useState(0);

  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const modelRef = useRef<LoadedModel | null>(null);
  const frameIdRef = useRef<number>(0);
  // Manual timing via performance.now() — avoids the deprecated THREE.Clock
  const clockRef = useRef<{ last: number; elapsed: number }>({ last: performance.now(), elapsed: 0 });
  const morphTargetsRef = useRef<Map<string, number>>(new Map());
  // All skinned meshes carrying morph targets (eyes, head, teeth)
  const morphMeshesRef = useRef<THREE.SkinnedMesh[]>([]);
  // Base Y position of the avatar (breathing oscillates around this)
  const baseYRef = useRef(0);

  // Active morph animations { name → { target, speed } }
  const animationsRef = useRef<Map<string, { target: number; current: number; speed: number }>>(new Map());

  // ---- Init ----
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const { scene, camera, renderer } = createScene(canvas, canvas.clientWidth, canvas.clientHeight);
    sceneRef.current = scene;
    cameraRef.current = camera;
    rendererRef.current = renderer;

    // Local state scoped to THIS effect invocation — safe under StrictMode's
    // double-invoke. `cancelled` prevents a cleaned-up invocation's async model
    // load from clobbering the live scene's refs; `loadedModel` keeps the animate
    // loop bound to this invocation's own model (not a shared ref).
    let cancelled = false;
    let loadedModel: LoadedModel | null = null;

    // Fallback sphere (local to this effect invocation)
    const fallback = createFallbackMesh();
    scene.add(fallback);
    baseYRef.current = fallback.position.y;

    // Load model
    setLoadProgress(0.1);
    loadModel(modelUrl)
      .then((model) => {
        if (cancelled) return; // StrictMode cleanup already disposed this scene
        // Remove THIS closure's fallback sphere (not a shared ref), so each
        // effect invocation cleans up its own scene's placeholder.
        scene.remove(fallback);
        (fallback.geometry as THREE.BufferGeometry).dispose();
        (fallback.material as THREE.Material).dispose();

        scene.add(model.group);
        loadedModel = model;
        modelRef.current = model;
        morphTargetsRef.current = model.morphTargets;
        morphMeshesRef.current = model.morphMeshes;
        baseYRef.current = model.group.position.y;
        setModelLoaded(true);
        setLoadProgress(1);

        // Dynamic framing: aim the camera at the model's head & upper body,
        // based on the actual bounding box (robust to any avatar proportions).
        const box = new THREE.Box3().setFromObject(model.group);
        const totalH = Math.max(box.max.y - box.min.y, 0.01);
        const headY = box.max.y - totalH * 0.12; // head center ≈ top 1/8 of body
        const frameH = totalH * 0.5;             // show top half (head + shoulders + chest)
        const dist = frameH / (2 * Math.tan((camera.fov * Math.PI / 180) / 2));
        camera.position.set(0, headY, dist);
        camera.lookAt(0, headY, 0);
      })
      .catch((err) => {
        if (cancelled) return;
        console.warn('[DigitalHuman] Model load failed, using fallback:', err.message);
        setLoadProgress(1); // mark as done even on error
      });

    // ---- Animation loop ----
    const animate = () => {
      frameIdRef.current = requestAnimationFrame(animate);

      const now = performance.now();
      const delta = (now - clockRef.current.last) / 1000; // seconds since last frame
      clockRef.current.elapsed += delta;
      clockRef.current.last = now;
      const totalTime = clockRef.current.elapsed;

      // Idle: gentle breathing on Y axis + subtle head sway
      const model = loadedModel?.group || fallback;
      if (model) {
        // Breathing — oscillate around the base Y (do NOT accumulate)
        const breath = Math.sin(totalTime * IDLE_BREATH_FREQUENCY * Math.PI * 2) * IDLE_BREATH_AMPLITUDE;
        model.position.y = baseYRef.current + breath;

        // Head sway (rotation around Y)
        const sway = Math.sin(totalTime * IDLE_SWAY_FREQUENCY * Math.PI * 2) * IDLE_SWAY_AMPLITUDE;
        model.rotation.y = sway;

        // Blink — every 2-5 seconds (ARKit: eyeBlinkLeft / eyeBlinkRight)
        const blinkPeriod = 3 + Math.sin(totalTime * 0.7) * 1;
        const blinkPhase = totalTime % blinkPeriod;
        if (blinkPhase < 0.15) {
          const blinkWeight = blinkPhase < 0.07
            ? blinkPhase / 0.07
            : 1 - (blinkPhase - 0.07) / 0.08;
          setMorphOnModel('eyeBlinkLeft', blinkWeight);
          setMorphOnModel('eyeBlinkRight', blinkWeight);
        } else {
          setMorphOnModel('eyeBlinkLeft', 0);
          setMorphOnModel('eyeBlinkRight', 0);
        }
      }

      // Process active morph animations
      const anims = animationsRef.current;
      anims.forEach((anim, name) => {
        anim.current += (anim.target - anim.current) * anim.speed * delta * 10;
        if (Math.abs(anim.current - anim.target) < 0.001) {
          anim.current = anim.target;
        }
        setMorphOnModel(name, anim.current);
      });

      renderer.render(scene, camera);
    };

    setReady(true);
    animate();

    return () => {
      cancelled = true;
      cancelAnimationFrame(frameIdRef.current);
      renderer.dispose();
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ---- Resize ----
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !cameraRef.current || !rendererRef.current) return;

    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        if (width === 0 || height === 0) return;

        cameraRef.current!.aspect = width / height;
        cameraRef.current!.updateProjectionMatrix();
        rendererRef.current!.setSize(width, height, false);
      }
    });

    observer.observe(canvas);
    return () => observer.disconnect();
  }, [canvasRef.current]); // eslint-disable-line react-hooks/exhaustive-deps

  // ---- Helper: set a morph weight across ALL facial morph meshes ----
  const setMorphOnModel = useCallback((name: string, value: number) => {
    const idx = morphTargetsRef.current.get(name);
    if (idx === undefined) return;
    const v = THREE.MathUtils.clamp(value, 0, 1);
    const meshes = morphMeshesRef.current;
    for (const mesh of meshes) {
      const infl = mesh.morphTargetInfluences;
      if (infl && idx < infl.length) {
        infl[idx] = v;
      }
    }
  }, []);

  // ---- Public API ----
  const setMorphWeight = useCallback((name: string, value: number) => {
    setMorphOnModel(name, value);
    // Also update animation tracking
    animationsRef.current.set(name, { target: value, current: value, speed: 5 });
  }, [setMorphOnModel]);

  const animateMorph = useCallback((name: string, target: number, duration: number) => {
    const speed = 1 / Math.max(duration, 0.05);
    const existing = animationsRef.current.get(name);
    animationsRef.current.set(name, {
      target,
      current: existing?.current ?? 0,
      speed,
    });
  }, []);

  const handleBoundary = useCallback((_e: TTSBoundaryEvent) => {
    // Lip-sync: open mouth briefly on word boundaries
    // Using the jawOpen morph target (ARKit blendshape)
    const mouthOpen = 0.4 + Math.random() * 0.3; // vary intensity
    animateMorph('jawOpen', mouthOpen, 0.08);
    // Schedule close
    setTimeout(() => {
      animateMorph('jawOpen', 0, 0.1);
    }, 100);
  }, [animateMorph]);

  const setExpression = useCallback(
    (expression: string, intensity = 1.0) => {
      // Map emotion keywords to ARKit blendshapes
      const exprMap: Record<string, Array<[string, number]>> = {
        neutral: [['browDownLeft', 0], ['browDownRight', 0], ['mouthSmileLeft', 0], ['mouthSmileRight', 0]],
        serious: [['browDownLeft', 0.6], ['browDownRight', 0.6], ['mouthSmileLeft', 0], ['mouthSmileRight', 0]],
        questioning: [['browInnerUp', 0.7], ['mouthPucker', 0.2]],
        relieved: [['browDownLeft', 0], ['browDownRight', 0], ['mouthSmileLeft', 0.3], ['mouthSmileRight', 0.3]],
        firm: [['browDownLeft', 0.5], ['browDownRight', 0.5], ['mouthFrownLeft', 0.3], ['mouthFrownRight', 0.3]],
        friendly: [['mouthSmileLeft', 0.5], ['mouthSmileRight', 0.5], ['cheekSquintLeft', 0.3], ['cheekSquintRight', 0.3]],
      };

      const targets = exprMap[expression] || exprMap.neutral;
      targets.forEach(([name, weight]) => {
        animateMorph(name, weight * intensity, 0.3);
      });
    },
    [animateMorph],
  );

  return {
    ready,
    modelLoaded,
    loadProgress,
    morphTargets: morphTargetsRef.current,
    setMorphWeight,
    animateMorph,
    handleBoundary,
    setExpression,
  };
}

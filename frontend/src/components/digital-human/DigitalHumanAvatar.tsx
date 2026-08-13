/** 3D 数字人头像 — Three.js Canvas 组件 */

import React, { useRef } from 'react';
import { Spin } from 'antd';
import { useDigitalHuman } from './useDigitalHuman';
import type { TTSBoundaryEvent } from './useSpeechSynthesis';

interface Props {
  /** Called when the 3D scene is ready */
  onReady?: (controls: {
    setMorphWeight: (name: string, value: number) => void;
    animateMorph: (name: string, target: number, duration: number) => void;
    handleBoundary: (e: TTSBoundaryEvent) => void;
    setExpression: (expression: string, intensity?: number) => void;
  }) => void;
  /** Optional custom model URL */
  modelUrl?: string;
  /** Width in pixels */
  width?: number;
  /** Height in pixels */
  height?: number;
}

const DigitalHumanAvatar: React.FC<Props> = ({
  onReady,
  modelUrl,
  width = 340,
  height = 400,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const readyCalledRef = useRef(false);

  const {
    ready,
    modelLoaded,
    loadProgress,
    setMorphWeight,
    animateMorph,
    handleBoundary,
    setExpression,
  } = useDigitalHuman({ canvasRef, modelUrl });

  // Notify parent once ready
  React.useEffect(() => {
    if (ready && !readyCalledRef.current) {
      readyCalledRef.current = true;
      onReady?.({
        setMorphWeight,
        animateMorph,
        handleBoundary,
        setExpression,
      });
    }
  }, [ready, onReady, setMorphWeight, animateMorph, handleBoundary, setExpression]);

  return (
    <div
      style={{
        position: 'relative',
        width,
        height,
        borderRadius: 20,
        overflow: 'hidden',
      }}
    >
      {/* Loading overlay */}
      {!modelLoaded && loadProgress < 1 && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'rgba(10,10,20,0.8)',
            zIndex: 2,
            borderRadius: 20,
          }}
        >
          <Spin size="default" />
          <span style={{ color: 'rgba(255,255,255,0.5)', fontSize: 12, marginTop: 12 }}>
            数字人加载中 {Math.round(loadProgress * 100)}%
          </span>
        </div>
      )}

      {/* Three.js Canvas */}
      <canvas
        ref={canvasRef}
        style={{
          width: '100%',
          height: '100%',
          display: 'block',
        }}
      />
    </div>
  );
};

export default DigitalHumanAvatar;

import React, { useRef, useState } from 'react';
import { Sphere, Html } from '@react-three/drei';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { getNodeColor, getNodeColorByType } from '../../utils/graphUtils';

const Node3D = ({
  node,
  position,
  size = 1,
  colorScheme = 'risk',
  selected = false,
  hovered = false,
  onClick,
  onPointerOver,
  onPointerOut,
}) => {
  const meshRef = useRef();
  const [pulseScale, setPulseScale] = useState(1);

  // Get node color based on scheme
  const getColor = () => {
    if (colorScheme === 'risk') {
      return getNodeColor(node.riskLevel);
    } else if (colorScheme === 'type') {
      return getNodeColorByType(node.type);
    }
    return '#00bcd4';
  };

  // Pulse animation for selected nodes
  useFrame((state) => {
    if (selected && meshRef.current) {
      const scale = 1 + Math.sin(state.clock.elapsedTime * 3) * 0.1;
      setPulseScale(scale);
    } else {
      setPulseScale(1);
    }

    // Gentle rotation for hovered nodes
    if (hovered && meshRef.current) {
      meshRef.current.rotation.y += 0.01;
    }
  });

  const finalSize = size * (hovered ? 1.2 : 1) * pulseScale;
  const color = new THREE.Color(getColor());

  return (
    <group position={position}>
      {/* Main sphere */}
      <Sphere
        ref={meshRef}
        args={[finalSize, 32, 32]}
        onClick={(e) => {
          e.stopPropagation();
          if (onClick) onClick(node);
        }}
        onPointerOver={(e) => {
          e.stopPropagation();
          document.body.style.cursor = 'pointer';
          if (onPointerOver) onPointerOver(node);
        }}
        onPointerOut={(e) => {
          e.stopPropagation();
          document.body.style.cursor = 'default';
          if (onPointerOut) onPointerOut(node);
        }}
      >
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={selected ? 0.5 : hovered ? 0.3 : 0.1}
          metalness={0.3}
          roughness={0.4}
        />
      </Sphere>

      {/* Selection ring */}
      {selected && (
        <mesh rotation={[Math.PI / 2, 0, 0]}>
          <ringGeometry args={[finalSize * 1.3, finalSize * 1.5, 32]} />
          <meshBasicMaterial color="#ffffff" transparent opacity={0.6} side={THREE.DoubleSide} />
        </mesh>
      )}

      {/* Label (only show for selected or hovered) */}
      {(selected || hovered) && (
        <Html distanceFactor={10} position={[0, finalSize + 0.5, 0]}>
          <div
            style={{
              background: 'rgba(0, 0, 0, 0.8)',
              color: 'white',
              padding: '4px 8px',
              borderRadius: '4px',
              fontSize: '12px',
              whiteSpace: 'nowrap',
              pointerEvents: 'none',
              userSelect: 'none',
            }}
          >
            {node.name}
          </div>
        </Html>
      )}

      {/* Risk indicator glow */}
      {node.riskLevel > 70 && (
        <pointLight
          color="#ff0000"
          intensity={node.riskLevel / 100}
          distance={finalSize * 3}
        />
      )}
    </group>
  );
};

export default Node3D;

// Made with Bob
import React, { useMemo } from 'react';
import { Line } from '@react-three/drei';
import * as THREE from 'three';
import { getEdgeColor } from '../../utils/graphUtils';

const Edge3D = ({
  source,
  target,
  riskContribution = 0,
  weight = 1,
  highlighted = false,
}) => {
  // Calculate line points
  const points = useMemo(() => {
    return [
      new THREE.Vector3(source.x, source.y, source.z),
      new THREE.Vector3(target.x, target.y, target.z),
    ];
  }, [source, target]);

  // Get edge color based on risk contribution
  const color = useMemo(() => {
    const colorStr = getEdgeColor(riskContribution);
    // Extract RGB values from rgba string
    const match = colorStr.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
    if (match) {
      return new THREE.Color(`rgb(${match[1]}, ${match[2]}, ${match[3]})`);
    }
    return new THREE.Color('#999999');
  }, [riskContribution]);

  // Calculate line width based on weight
  const lineWidth = useMemo(() => {
    return Math.max(0.5, Math.min(weight * 2, 3)) * (highlighted ? 1.5 : 1);
  }, [weight, highlighted]);

  // Calculate opacity
  const opacity = highlighted ? 0.9 : 0.4;

  return (
    <Line
      points={points}
      color={color}
      lineWidth={lineWidth}
      transparent
      opacity={opacity}
    />
  );
};

export default Edge3D;

// Made with Bob
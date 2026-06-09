import React from 'react';
import { Stars, Grid } from '@react-three/drei';

const Environment = ({ showGrid = true, showStars = true }) => {
  return (
    <>
      {/* Starfield background */}
      {showStars && (
        <Stars
          radius={100}
          depth={50}
          count={5000}
          factor={4}
          saturation={0}
          fade
          speed={1}
        />
      )}

      {/* Grid floor for spatial reference */}
      {showGrid && (
        <Grid
          args={[100, 100]}
          cellSize={5}
          cellThickness={0.5}
          cellColor="#6f6f6f"
          sectionSize={20}
          sectionThickness={1}
          sectionColor="#9d4b4b"
          fadeDistance={100}
          fadeStrength={1}
          followCamera={false}
          infiniteGrid
        />
      )}

      {/* Fog for depth perception */}
      <fog attach="fog" args={['#0a0e27', 50, 200]} />
    </>
  );
};

export default Environment;

// Made with Bob
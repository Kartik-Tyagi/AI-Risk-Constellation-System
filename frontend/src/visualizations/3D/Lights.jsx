import React from 'react';

const Lights = () => {
  return (
    <>
      {/* Ambient light for overall illumination */}
      <ambientLight intensity={0.3} />

      {/* Main directional light (sun-like) */}
      <directional Light
        position={[10, 10, 5]}
        intensity={0.8}
        castShadow
        shadow-mapSize-width={2048}
        shadow-mapSize-height={2048}
      />

      {/* Fill light from opposite side */}
      <directionalLight
        position={[-10, -10, -5]}
        intensity={0.3}
      />

      {/* Top light for better visibility */}
      <directionalLight
        position={[0, 20, 0]}
        intensity={0.4}
      />

      {/* Hemisphere light for natural sky/ground lighting */}
      <hemisphereLight
        skyColor="#ffffff"
        groundColor="#444444"
        intensity={0.4}
      />

      {/* Point lights for dramatic effect */}
      <pointLight position={[0, 0, 10]} intensity={0.5} color="#00bcd4" />
      <pointLight position={[0, 0, -10]} intensity={0.5} color="#ff4081" />
    </>
  );
};

export default Lights;

// Made with Bob
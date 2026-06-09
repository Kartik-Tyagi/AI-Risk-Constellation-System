import React, { useRef, useState, useEffect, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, PerspectiveCamera } from '@react-three/drei';
import { Box, CircularProgress } from '@mui/material';
import * as THREE from 'three';
import Node3D from './3D/Node3D';
import Edge3D from './3D/Edge3D';
import Lights from './3D/Lights';
import Environment from './3D/Environment';
import { transformGraphData, calculateNodeSize } from '../utils/graphUtils';

// 3D Force Simulation Component
const ForceGraph3D = ({
  nodes,
  links,
  colorScheme,
  sizeBy,
  selectedNode,
  hoveredNode,
  onNodeClick,
  onNodeHover,
}) => {
  const groupRef = useRef();
  const [positions, setPositions] = useState(new Map());

  // Initialize node positions in 3D space
  useEffect(() => {
    const newPositions = new Map();
    
    nodes.forEach((node, index) => {
      // Distribute nodes in a sphere
      const phi = Math.acos(-1 + (2 * index) / nodes.length);
      const theta = Math.sqrt(nodes.length * Math.PI) * phi;
      const radius = 30;

      newPositions.set(node.id, {
        x: radius * Math.cos(theta) * Math.sin(phi),
        y: radius * Math.sin(theta) * Math.sin(phi),
        z: radius * Math.cos(phi),
        vx: 0,
        vy: 0,
        vz: 0,
      });
    });

    setPositions(newPositions);
  }, [nodes]);

  // Simple 3D force simulation
  useFrame(() => {
    if (positions.size === 0) return;

    const newPositions = new Map(positions);
    const alpha = 0.1;
    const linkStrength = 0.1;
    const chargeStrength = -50;
    const centerStrength = 0.01;

    // Apply forces
    nodes.forEach((node) => {
      const pos = newPositions.get(node.id);
      if (!pos) return;

      let fx = 0, fy = 0, fz = 0;

      // Center force
      fx -= pos.x * centerStrength;
      fy -= pos.y * centerStrength;
      fz -= pos.z * centerStrength;

      // Charge force (repulsion between nodes)
      nodes.forEach((otherNode) => {
        if (node.id === otherNode.id) return;
        const otherPos = newPositions.get(otherNode.id);
        if (!otherPos) return;

        const dx = pos.x - otherPos.x;
        const dy = pos.y - otherPos.y;
        const dz = pos.z - otherPos.z;
        const distSq = dx * dx + dy * dy + dz * dz + 0.01;
        const dist = Math.sqrt(distSq);

        const force = chargeStrength / distSq;
        fx += (dx / dist) * force;
        fy += (dy / dist) * force;
        fz += (dz / dist) * force;
      });

      // Link force (attraction along edges)
      links.forEach((link) => {
        const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
        const targetId = typeof link.target === 'object' ? link.target.id : link.target;

        if (node.id === sourceId) {
          const targetPos = newPositions.get(targetId);
          if (targetPos) {
            const dx = targetPos.x - pos.x;
            const dy = targetPos.y - pos.y;
            const dz = targetPos.z - pos.z;
            fx += dx * linkStrength * link.weight;
            fy += dy * linkStrength * link.weight;
            fz += dz * linkStrength * link.weight;
          }
        } else if (node.id === targetId) {
          const sourcePos = newPositions.get(sourceId);
          if (sourcePos) {
            const dx = sourcePos.x - pos.x;
            const dy = sourcePos.y - pos.y;
            const dz = sourcePos.z - pos.z;
            fx += dx * linkStrength * link.weight;
            fy += dy * linkStrength * link.weight;
            fz += dz * linkStrength * link.weight;
          }
        }
      });

      // Update velocity and position
      pos.vx = (pos.vx + fx) * alpha;
      pos.vy = (pos.vy + fy) * alpha;
      pos.vz = (pos.vz + fz) * alpha;

      pos.x += pos.vx;
      pos.y += pos.vy;
      pos.z += pos.vz;
    });

    setPositions(newPositions);
  });

  // Render edges
  const edgeElements = useMemo(() => {
    return links.map((link, index) => {
      const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
      const targetId = typeof link.target === 'object' ? link.target.id : link.target;
      
      const sourcePos = positions.get(sourceId);
      const targetPos = positions.get(targetId);

      if (!sourcePos || !targetPos) return null;

      const isHighlighted =
        (selectedNode && (sourceId === selectedNode.id || targetId === selectedNode.id)) ||
        (hoveredNode && (sourceId === hoveredNode.id || targetId === hoveredNode.id));

      return (
        <Edge3D
          key={`edge-${index}`}
          source={sourcePos}
          target={targetPos}
          riskContribution={link.riskContribution}
          weight={link.weight}
          highlighted={isHighlighted}
        />
      );
    });
  }, [links, positions, selectedNode, hoveredNode]);

  // Render nodes
  const nodeElements = useMemo(() => {
    return nodes.map((node) => {
      const pos = positions.get(node.id);
      if (!pos) return null;

      const size = calculateNodeSize(node, { sizeBy }) / 10; // Scale down for 3D
      const isSelected = selectedNode?.id === node.id;
      const isHovered = hoveredNode?.id === node.id;

      return (
        <Node3D
          key={node.id}
          node={node}
          position={[pos.x, pos.y, pos.z]}
          size={size}
          colorScheme={colorScheme}
          selected={isSelected}
          hovered={isHovered}
          onClick={onNodeClick}
          onPointerOver={onNodeHover}
          onPointerOut={() => onNodeHover && onNodeHover(null)}
        />
      );
    });
  }, [nodes, positions, colorScheme, sizeBy, selectedNode, hoveredNode, onNodeClick, onNodeHover]);

  return (
    <group ref={groupRef}>
      {edgeElements}
      {nodeElements}
    </group>
  );
};

// Main Component
const RiskGraph3D = ({
  data,
  width = 800,
  height = 600,
  onNodeClick,
  onNodeHover,
  colorScheme = 'risk',
  sizeBy = 'riskScore',
  showGrid = true,
  showStars = true,
}) => {
  const [selectedNode, setSelectedNode] = useState(null);
  const [hoveredNode, setHoveredNode] = useState(null);

  // Transform graph data
  const graphData = transformGraphData(data);

  const handleNodeClick = (node) => {
    setSelectedNode(node);
    if (onNodeClick) onNodeClick(node);
  };

  const handleNodeHover = (node) => {
    setHoveredNode(node);
    if (onNodeHover) onNodeHover(node);
  };

  if (!data || !graphData.nodes.length) {
    return (
      <Box
        sx={{
          width,
          height,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: 'background.paper',
          borderRadius: 1,
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box
      sx={{
        width,
        height,
        backgroundColor: '#0a0e27',
        borderRadius: 1,
        overflow: 'hidden',
        position: 'relative',
      }}
    >
      <Canvas>
        {/* Camera */}
        <PerspectiveCamera makeDefault position={[0, 0, 80]} fov={75} />

        {/* Controls */}
        <OrbitControls
          enableDamping
          dampingFactor={0.05}
          rotateSpeed={0.5}
          zoomSpeed={0.8}
          minDistance={20}
          maxDistance={200}
        />

        {/* Lighting */}
        <Lights />

        {/* Environment */}
        <Environment showGrid={showGrid} showStars={showStars} />

        {/* Graph */}
        <ForceGraph3D
          nodes={graphData.nodes}
          links={graphData.links}
          colorScheme={colorScheme}
          sizeBy={sizeBy}
          selectedNode={selectedNode}
          hoveredNode={hoveredNode}
          onNodeClick={handleNodeClick}
          onNodeHover={handleNodeHover}
        />
      </Canvas>

      {/* Selected node info */}
      {selectedNode && (
        <Box
          sx={{
            position: 'absolute',
            bottom: 16,
            left: 16,
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            padding: 2,
            borderRadius: 1,
            border: '1px solid',
            borderColor: 'divider',
            color: 'white',
          }}
        >
          <Box sx={{ fontWeight: 600 }}>{selectedNode.name}</Box>
          <Box sx={{ fontSize: '0.875rem', opacity: 0.8 }}>
            Risk: {selectedNode.riskLevel.toFixed(1)}%
          </Box>
        </Box>
      )}
    </Box>
  );
};

export default RiskGraph3D;

// Made with Bob
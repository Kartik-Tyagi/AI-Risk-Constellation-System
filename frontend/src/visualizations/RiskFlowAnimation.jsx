import React, { useRef, useEffect, useState } from 'react';
import * as d3 from 'd3';
import { Box, IconButton, Slider, Typography, Stack } from '@mui/material';
import { PlayArrow, Pause, Replay } from '@mui/icons-material';

const RiskFlowAnimation = ({
  data,
  width = 800,
  height = 600,
  particleCount = 100,
  speed = 1,
}) => {
  const canvasRef = useRef(null);
  const animationRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(true);
  const [animationSpeed, setAnimationSpeed] = useState(speed);
  const particlesRef = useRef([]);

  // Initialize particles
  useEffect(() => {
    if (!data || !data.nodes || !data.links) return;

    const particles = [];
    
    // Create particles along edges
    data.links.forEach((link) => {
      const sourceNode = data.nodes.find((n) => n.id === link.source || n.id === link.source.id);
      const targetNode = data.nodes.find((n) => n.id === link.target || n.id === link.target.id);
      
      if (!sourceNode || !targetNode) return;

      // Number of particles based on risk contribution
      const numParticles = Math.ceil(Math.abs(link.riskContribution || 1) / 10);
      
      for (let i = 0; i < numParticles; i++) {
        particles.push({
          sourceX: sourceNode.x || Math.random() * width,
          sourceY: sourceNode.y || Math.random() * height,
          targetX: targetNode.x || Math.random() * width,
          targetY: targetNode.y || Math.random() * height,
          progress: Math.random(), // Random starting position
          speed: 0.005 + Math.random() * 0.01,
          size: 2 + Math.random() * 3,
          color: link.riskContribution > 0 ? '#f44336' : '#4caf50',
          opacity: 0.6 + Math.random() * 0.4,
        });
      }
    });

    particlesRef.current = particles;
  }, [data, width, height]);

  // Animation loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    canvas.width = width;
    canvas.height = height;

    const animate = () => {
      if (!isPlaying) return;

      // Clear canvas with fade effect
      ctx.fillStyle = 'rgba(10, 14, 39, 0.1)';
      ctx.fillRect(0, 0, width, height);

      // Update and draw particles
      particlesRef.current.forEach((particle) => {
        // Update progress
        particle.progress += particle.speed * animationSpeed;
        
        // Reset if reached target
        if (particle.progress >= 1) {
          particle.progress = 0;
        }

        // Calculate current position
        const x = particle.sourceX + (particle.targetX - particle.sourceX) * particle.progress;
        const y = particle.sourceY + (particle.targetY - particle.sourceY) * particle.progress;

        // Draw particle
        ctx.beginPath();
        ctx.arc(x, y, particle.size, 0, Math.PI * 2);
        ctx.fillStyle = particle.color;
        ctx.globalAlpha = particle.opacity;
        ctx.fill();

        // Draw trail
        if (particle.progress > 0.05) {
          const trailX = particle.sourceX + (particle.targetX - particle.sourceX) * (particle.progress - 0.05);
          const trailY = particle.sourceY + (particle.targetY - particle.sourceY) * (particle.progress - 0.05);
          
          ctx.beginPath();
          ctx.moveTo(trailX, trailY);
          ctx.lineTo(x, y);
          ctx.strokeStyle = particle.color;
          ctx.lineWidth = particle.size / 2;
          ctx.globalAlpha = particle.opacity * 0.5;
          ctx.stroke();
        }
      });

      ctx.globalAlpha = 1;
      animationRef.current = requestAnimationFrame(animate);
    };

    if (isPlaying) {
      animate();
    }

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isPlaying, animationSpeed, width, height]);

  const handlePlayPause = () => {
    setIsPlaying(!isPlaying);
  };

  const handleRestart = () => {
    particlesRef.current.forEach((particle) => {
      particle.progress = Math.random();
    });
  };

  const handleSpeedChange = (event, newValue) => {
    setAnimationSpeed(newValue);
  };

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
      <canvas
        ref={canvasRef}
        style={{
          display: 'block',
          width: '100%',
          height: '100%',
        }}
      />

      {/* Controls */}
      <Box
        sx={{
          position: 'absolute',
          bottom: 16,
          left: '50%',
          transform: 'translateX(-50%)',
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          padding: 2,
          borderRadius: 1,
          display: 'flex',
          alignItems: 'center',
          gap: 2,
        }}
      >
        <IconButton onClick={handlePlayPause} size="small" sx={{ color: 'white' }}>
          {isPlaying ? <Pause /> : <PlayArrow />}
        </IconButton>

        <IconButton onClick={handleRestart} size="small" sx={{ color: 'white' }}>
          <Replay />
        </IconButton>

        <Stack spacing={1} sx={{ minWidth: 200 }}>
          <Typography variant="caption" sx={{ color: 'white' }}>
            Speed: {animationSpeed.toFixed(1)}x
          </Typography>
          <Slider
            value={animationSpeed}
            onChange={handleSpeedChange}
            min={0.1}
            max={5}
            step={0.1}
            size="small"
            sx={{ color: 'primary.main' }}
          />
        </Stack>
      </Box>

      {/* Legend */}
      <Box
        sx={{
          position: 'absolute',
          top: 16,
          right: 16,
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          padding: 2,
          borderRadius: 1,
        }}
      >
        <Typography variant="caption" sx={{ color: 'white', display: 'block', mb: 1 }}>
          Risk Flow
        </Typography>
        <Stack spacing={0.5}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Box
              sx={{
                width: 12,
                height: 12,
                borderRadius: '50%',
                backgroundColor: '#f44336',
              }}
            />
            <Typography variant="caption" sx={{ color: 'white' }}>
              Increasing Risk
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Box
              sx={{
                width: 12,
                height: 12,
                borderRadius: '50%',
                backgroundColor: '#4caf50',
              }}
            />
            <Typography variant="caption" sx={{ color: 'white' }}>
              Decreasing Risk
            </Typography>
          </Box>
        </Stack>
      </Box>
    </Box>
  );
};

export default RiskFlowAnimation;

// Made with Bob
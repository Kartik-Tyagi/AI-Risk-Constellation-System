import React, { useRef, useEffect, useState } from 'react';
import { Box, useTheme, useMediaQuery, IconButton, Tooltip } from '@mui/material';
import {
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  CenterFocusStrong as CenterIcon,
} from '@mui/icons-material';
import RiskGraph2D from '../visualizations/RiskGraph2D';

const ResponsiveGraph = ({ data, onNodeClick }) => {
  const theme = useTheme();
  const containerRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const [lastTouch, setLastTouch] = useState(null);
  const [lastPinchDistance, setLastPinchDistance] = useState(null);

  // Responsive breakpoints
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.between('sm', 'md'));
  const isDesktop = useMediaQuery(theme.breakpoints.up('md'));

  // Update dimensions on resize
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const { width, height } = containerRef.current.getBoundingClientRect();
        setDimensions({ width, height: height || 400 });
      }
    };

    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  // Touch gesture handlers
  const handleTouchStart = (e) => {
    if (e.touches.length === 1) {
      // Single touch - pan
      setIsPanning(true);
      setLastTouch({ x: e.touches[0].clientX, y: e.touches[0].clientY });
    } else if (e.touches.length === 2) {
      // Two touches - pinch zoom
      const distance = getTouchDistance(e.touches[0], e.touches[1]);
      setLastPinchDistance(distance);
    }
  };

  const handleTouchMove = (e) => {
    e.preventDefault();

    if (e.touches.length === 1 && isPanning && lastTouch) {
      // Pan
      const deltaX = e.touches[0].clientX - lastTouch.x;
      const deltaY = e.touches[0].clientY - lastTouch.y;
      
      setPan((prev) => ({
        x: prev.x + deltaX,
        y: prev.y + deltaY,
      }));
      
      setLastTouch({ x: e.touches[0].clientX, y: e.touches[0].clientY });
    } else if (e.touches.length === 2 && lastPinchDistance) {
      // Pinch zoom
      const distance = getTouchDistance(e.touches[0], e.touches[1]);
      const scale = distance / lastPinchDistance;
      
      setZoom((prev) => Math.max(0.5, Math.min(3, prev * scale)));
      setLastPinchDistance(distance);
    }
  };

  const handleTouchEnd = () => {
    setIsPanning(false);
    setLastTouch(null);
    setLastPinchDistance(null);
  };

  const getTouchDistance = (touch1, touch2) => {
    const dx = touch1.clientX - touch2.clientX;
    const dy = touch1.clientY - touch2.clientY;
    return Math.sqrt(dx * dx + dy * dy);
  };

  // Mouse wheel zoom
  const handleWheel = (e) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    setZoom((prev) => Math.max(0.5, Math.min(3, prev * delta)));
  };

  // Zoom controls
  const handleZoomIn = () => {
    setZoom((prev) => Math.min(3, prev * 1.2));
  };

  const handleZoomOut = () => {
    setZoom((prev) => Math.max(0.5, prev / 1.2));
  };

  const handleResetView = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  // Simplify data for mobile
  const getSimplifiedData = () => {
    if (!data) return null;

    if (isMobile) {
      // Show only top nodes on mobile
      return {
        nodes: data.nodes.slice(0, 20),
        edges: data.edges.filter(
          (edge) =>
            data.nodes.slice(0, 20).some((n) => n.id === edge.source) &&
            data.nodes.slice(0, 20).some((n) => n.id === edge.target)
        ),
      };
    } else if (isTablet) {
      // Show more nodes on tablet
      return {
        nodes: data.nodes.slice(0, 50),
        edges: data.edges.filter(
          (edge) =>
            data.nodes.slice(0, 50).some((n) => n.id === edge.source) &&
            data.nodes.slice(0, 50).some((n) => n.id === edge.target)
        ),
      };
    }

    return data;
  };

  const simplifiedData = getSimplifiedData();

  return (
    <Box
      ref={containerRef}
      sx={{
        position: 'relative',
        width: '100%',
        height: isMobile ? 300 : isTablet ? 400 : 600,
        overflow: 'hidden',
        touchAction: 'none',
      }}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
      onWheel={handleWheel}
    >
      {/* Zoom Controls */}
      <Box
        sx={{
          position: 'absolute',
          top: 16,
          right: 16,
          zIndex: 10,
          display: 'flex',
          flexDirection: 'column',
          gap: 1,
          backgroundColor: 'background.paper',
          borderRadius: 1,
          boxShadow: 2,
          p: 0.5,
        }}
      >
        <Tooltip title="Zoom In" placement="left">
          <IconButton size="small" onClick={handleZoomIn}>
            <ZoomInIcon />
          </IconButton>
        </Tooltip>
        <Tooltip title="Zoom Out" placement="left">
          <IconButton size="small" onClick={handleZoomOut}>
            <ZoomOutIcon />
          </IconButton>
        </Tooltip>
        <Tooltip title="Reset View" placement="left">
          <IconButton size="small" onClick={handleResetView}>
            <CenterIcon />
          </IconButton>
        </Tooltip>
      </Box>

      {/* Graph */}
      <Box
        sx={{
          transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
          transformOrigin: 'center center',
          transition: isPanning ? 'none' : 'transform 0.2s ease-out',
        }}
      >
        {simplifiedData && (
          <RiskGraph2D
            data={simplifiedData}
            width={dimensions.width}
            height={dimensions.height}
            onNodeClick={onNodeClick}
            nodeSize={isMobile ? 4 : isTablet ? 6 : 8}
            fontSize={isMobile ? 10 : isTablet ? 11 : 12}
            showLabels={!isMobile}
          />
        )}
      </Box>

      {/* Mobile Instructions */}
      {isMobile && (
        <Box
          sx={{
            position: 'absolute',
            bottom: 16,
            left: '50%',
            transform: 'translateX(-50%)',
            backgroundColor: 'rgba(0, 0, 0, 0.7)',
            color: 'white',
            px: 2,
            py: 1,
            borderRadius: 1,
            fontSize: '0.75rem',
            pointerEvents: 'none',
          }}
        >
          Pinch to zoom • Drag to pan
        </Box>
      )}
    </Box>
  );
};

export default ResponsiveGraph;

// Made with Bob
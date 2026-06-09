import React, { useState, useEffect, useRef } from 'react';
import { Box, CircularProgress, Typography, Paper, Slider, FormControlLabel, Switch } from '@mui/material';
import RiskGraph2D from '../visualizations/RiskGraph2D';
import GraphLegend from '../visualizations/GraphLegend';
import { get } from '../services/api';

const RiskConstellation = () => {
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [showLabels, setShowLabels] = useState(true);
  const [minRisk, setMinRisk] = useState(0);
  const containerRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width: 1200, height: 700 });

  useEffect(() => {
    const update = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.offsetWidth,
          height: containerRef.current.offsetHeight,
        });
      }
    };
    update();
    window.addEventListener('resize', update);
    return () => window.removeEventListener('resize', update);
  }, []);

  useEffect(() => {
    setLoading(true);
    get('/graph/constellation', { min_risk_score: minRisk })
      .then(res => setGraphData(res.data))
      .catch(err => setError(err.message || 'Failed to load graph'))
      .finally(() => setLoading(false));
  }, [minRisk]);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh', bgcolor: 'background.default' }}>
      {/* Header Controls */}
      <Paper sx={{ p: 1.5, display: 'flex', alignItems: 'center', gap: 3, zIndex: 10 }} elevation={2}>
        <Typography variant="h6" sx={{ minWidth: 160 }}>Risk Constellation</Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 220 }}>
          <Typography variant="body2" color="text.secondary" sx={{ minWidth: 80 }}>
            Min Risk: {minRisk}
          </Typography>
          <Slider
            value={minRisk}
            onChange={(_, v) => setMinRisk(v)}
            min={0}
            max={80}
            step={5}
            size="small"
            sx={{ width: 120 }}
          />
        </Box>
        <FormControlLabel
          control={<Switch checked={showLabels} onChange={e => setShowLabels(e.target.checked)} size="small" />}
          label="Labels"
        />
        {graphData && (
          <Typography variant="caption" color="text.secondary">
            {graphData.total_nodes} nodes · {graphData.total_edges} edges
          </Typography>
        )}
        {selectedNode && (
          <Paper sx={{ px: 2, py: 0.5, bgcolor: 'primary.dark' }} elevation={1}>
            <Typography variant="body2">
              <strong>{selectedNode.name}</strong> · {selectedNode.type} · Risk: {selectedNode.risk_score?.toFixed(1)}
            </Typography>
          </Paper>
        )}
      </Paper>

      {/* Graph Area */}
      <Box ref={containerRef} sx={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
        {loading && (
          <Box sx={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 5 }}>
            <CircularProgress />
          </Box>
        )}
        {error && (
          <Box sx={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Typography color="error">{error}</Typography>
          </Box>
        )}
        {graphData && !loading && (
          <RiskGraph2D
            data={graphData}
            width={dimensions.width}
            height={dimensions.height}
            showLabels={showLabels}
            colorScheme="risk"
            onNodeClick={node => setSelectedNode(node)}
          />
        )}
        {graphData && <GraphLegend sx={{ position: 'absolute', bottom: 16, right: 16 }} />}
      </Box>
    </Box>
  );
};

export default RiskConstellation;

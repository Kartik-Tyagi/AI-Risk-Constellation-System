import React from 'react';
import {
  Paper,
  Typography,
  Box,
  IconButton,
  Tooltip,
} from '@mui/material';
import { Close as CloseIcon, Settings as SettingsIcon, Fullscreen as FullscreenIcon } from '@mui/icons-material';
import RiskGraph2D from '../../visualizations/RiskGraph2D';
import { useRiskData } from '../../hooks/useRiskData';

const GraphWidget = ({ widgetId, title, onRemove, onSettings, settings }) => {
  const { data: graphData } = useRiskData('/graph/risk-network');

  return (
    <Paper sx={{ p: 2, height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">{title}</Typography>
        <Box>
          <Tooltip title="Fullscreen">
            <IconButton size="small">
              <FullscreenIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Settings">
            <IconButton size="small" onClick={() => onSettings({})}>
              <SettingsIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Remove">
            <IconButton size="small" onClick={onRemove}>
              <CloseIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      <Box sx={{ flexGrow: 1, minHeight: 0 }}>
        {graphData && (
          <RiskGraph2D
            data={graphData}
            width={600}
            height={300}
          />
        )}
      </Box>
    </Paper>
  );
};

export default GraphWidget;

// Made with Bob
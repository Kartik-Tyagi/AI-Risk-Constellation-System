import React, { useState } from 'react';
import {
  Paper,
  Typography,
  Box,
  IconButton,
  Tooltip,
  ToggleButtonGroup,
  ToggleButton,
} from '@mui/material';
import { Close as CloseIcon, Settings as SettingsIcon } from '@mui/icons-material';
import TimeSeriesChart from '../../visualizations/TimeSeriesChart';
import RiskDistribution from '../../visualizations/RiskDistribution';
import { useRiskData } from '../../hooks/useRiskData';

const ChartWidget = ({ widgetId, title, onRemove, onSettings, settings }) => {
  const [chartType, setChartType] = useState(settings?.chartType || 'timeseries');
  const { data: chartData } = useRiskData(`/risk/${chartType}-data`);

  const handleChartTypeChange = (event, newType) => {
    if (newType !== null) {
      setChartType(newType);
      onSettings({ ...settings, chartType: newType });
    }
  };

  return (
    <Paper sx={{ p: 2, height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">{title}</Typography>
        <Box>
          <Tooltip title="Settings">
            <IconButton size="small" onClick={() => onSettings(settings)}>
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

      <Box sx={{ mb: 2 }}>
        <ToggleButtonGroup
          value={chartType}
          exclusive
          onChange={handleChartTypeChange}
          size="small"
        >
          <ToggleButton value="timeseries">Time Series</ToggleButton>
          <ToggleButton value="distribution">Distribution</ToggleButton>
        </ToggleButtonGroup>
      </Box>

      <Box sx={{ flexGrow: 1, minHeight: 0 }}>
        {chartType === 'timeseries' && chartData && (
          <TimeSeriesChart data={chartData} width={600} height={250} />
        )}
        {chartType === 'distribution' && chartData && (
          <RiskDistribution data={chartData} width={600} height={250} />
        )}
      </Box>
    </Paper>
  );
};

export default ChartWidget;

// Made with Bob
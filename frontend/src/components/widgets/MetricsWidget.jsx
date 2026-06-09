import React from 'react';
import {
  Paper,
  Typography,
  Box,
  IconButton,
  Tooltip,
  Grid,
  Card,
  CardContent,
} from '@mui/material';
import { Close as CloseIcon, Settings as SettingsIcon } from '@mui/icons-material';
import { useRiskData } from '../../hooks/useRiskData';

const MetricsWidget = ({ widgetId, title, onRemove, onSettings, settings }) => {
  const { data: metrics } = useRiskData('/risk/metrics');

  const metricsList = [
    { label: 'Avg Risk Score', value: metrics?.avg_risk_score?.toFixed(2) || '0.00', unit: '' },
    { label: 'Max Risk', value: metrics?.max_risk?.toFixed(2) || '0.00', unit: '' },
    { label: 'Entities Monitored', value: metrics?.total_entities || '0', unit: '' },
    { label: 'Correlations', value: metrics?.total_correlations || '0', unit: '' },
    { label: 'Cascade Depth', value: metrics?.avg_cascade_depth?.toFixed(1) || '0.0', unit: 'levels' },
    { label: 'Update Frequency', value: metrics?.update_frequency || '0', unit: '/min' },
  ];

  return (
    <Paper sx={{ p: 2, height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">{title}</Typography>
        <Box>
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

      <Grid container spacing={1} sx={{ flexGrow: 1 }}>
        {metricsList.map((metric, idx) => (
          <Grid item xs={6} key={idx}>
            <Card sx={{ height: '100%', backgroundColor: 'background.default' }}>
              <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
                <Typography variant="caption" color="text.secondary" display="block">
                  {metric.label}
                </Typography>
                <Typography variant="h6">
                  {metric.value}
                  {metric.unit && (
                    <Typography component="span" variant="caption" color="text.secondary" sx={{ ml: 0.5 }}>
                      {metric.unit}
                    </Typography>
                  )}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Paper>
  );
};

export default MetricsWidget;

// Made with Bob
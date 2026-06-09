import React, { useState, useEffect } from 'react';
import {
  Paper,
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  IconButton,
  Tooltip,
  CircularProgress,
} from '@mui/material';
import {
  Close as CloseIcon,
  Settings as SettingsIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import { get } from '../../services/api';

const RiskSummaryWidget = ({ widgetId, title, onRemove, onSettings, settings }) => {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    get('/risk/summary')
      .then(res => setSummary(res.data))
      .catch(err => setError(err.message || 'Failed to load'))
      .finally(() => setLoading(false));
  }, []);

  const getRiskColor = (level) => {
    switch (level?.toLowerCase()) {
      case 'low':
        return 'success.main';
      case 'medium':
        return 'warning.main';
      case 'high':
        return 'error.main';
      default:
        return 'text.secondary';
    }
  };

  const getTrendIcon = (trend) => {
    if (trend > 0) return <TrendingUpIcon color="error" />;
    if (trend < 0) return <TrendingDownIcon color="success" />;
    return null;
  };

  if (loading) {
    return (
      <Paper sx={{ p: 2, height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <CircularProgress />
      </Paper>
    );
  }

  if (error) {
    return (
      <Paper sx={{ p: 2, height: '100%' }}>
        <Typography color="error">Error loading risk summary</Typography>
      </Paper>
    );
  }

  return (
    <Paper sx={{ p: 2, height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Widget Header */}
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

      {/* Widget Content */}
      <Grid container spacing={2} sx={{ flexGrow: 1 }}>
        <Grid item xs={6}>
          <Card sx={{ height: '100%', backgroundColor: 'background.default' }}>
            <CardContent>
              <Typography variant="caption" color="text.secondary">
                Overall Risk
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="h4" sx={{ color: getRiskColor(summary?.overall_risk_level) }}>
                  {summary?.overall_risk_score?.toFixed(1) || '0.0'}
                </Typography>
                {getTrendIcon(summary?.risk_trend || 0)}
              </Box>
              <Typography variant="caption" color="text.secondary">
                {summary?.overall_risk_level || 'N/A'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={6}>
          <Card sx={{ height: '100%', backgroundColor: 'background.default' }}>
            <CardContent>
              <Typography variant="caption" color="text.secondary">
                High Risk Entities
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="h4" color="error.main">
                  {summary?.high_risk_count || 0}
                </Typography>
                <WarningIcon color="error" />
              </Box>
              <Typography variant="caption" color="text.secondary">
                of {summary?.total_entities || 0} total
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={6}>
          <Card sx={{ height: '100%', backgroundColor: 'background.default' }}>
            <CardContent>
              <Typography variant="caption" color="text.secondary">
                Active Alerts
              </Typography>
              <Typography variant="h4" color="warning.main">
                {summary?.active_alerts || 0}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {summary?.critical_alerts || 0} critical
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={6}>
          <Card sx={{ height: '100%', backgroundColor: 'background.default' }}>
            <CardContent>
              <Typography variant="caption" color="text.secondary">
                Risk Volatility
              </Typography>
              <Typography variant="h4">
                {summary?.risk_volatility?.toFixed(2) || '0.00'}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                24h change
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Paper>
  );
};

export default RiskSummaryWidget;

// Made with Bob
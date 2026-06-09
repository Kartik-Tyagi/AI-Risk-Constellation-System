import React, { useState, useEffect } from 'react';
import {
  Paper,
  Typography,
  Box,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Tooltip,
  CircularProgress,
  Chip,
  Badge,
} from '@mui/material';
import {
  Close as CloseIcon,
  Settings as SettingsIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { useRiskData } from '../../hooks/useRiskData';

const AlertsWidget = ({ widgetId, title, onRemove, onSettings, settings }) => {
  const { data: alerts, loading, error } = useRiskData('/alerts');

  const getSeverityIcon = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical':
        return <ErrorIcon color="error" />;
      case 'warning':
        return <WarningIcon color="warning" />;
      case 'info':
        return <InfoIcon color="info" />;
      default:
        return <InfoIcon />;
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical':
        return 'error';
      case 'warning':
        return 'warning';
      case 'info':
        return 'info';
      default:
        return 'default';
    }
  };

  if (loading) {
    return (
      <Paper sx={{ p: 2, height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <CircularProgress />
      </Paper>
    );
  }

  return (
    <Paper sx={{ p: 2, height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography variant="h6">{title}</Typography>
          <Badge badgeContent={alerts?.length || 0} color="error" />
        </Box>
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

      <List sx={{ flexGrow: 1, overflow: 'auto' }}>
        {alerts?.slice(0, 10).map((alert, idx) => (
          <ListItem
            key={idx}
            sx={{
              borderLeft: 3,
              borderColor: `${getSeverityColor(alert.severity)}.main`,
              mb: 1,
              backgroundColor: 'background.default',
            }}
          >
            <Box sx={{ mr: 2 }}>{getSeverityIcon(alert.severity)}</Box>
            <ListItemText
              primary={alert.message || 'Alert'}
              secondary={
                <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
                  <Chip label={alert.severity} color={getSeverityColor(alert.severity)} size="small" />
                  <Typography variant="caption" color="text.secondary">
                    {new Date(alert.timestamp).toLocaleTimeString()}
                  </Typography>
                </Box>
              }
            />
          </ListItem>
        ))}
        {(!alerts || alerts.length === 0) && (
          <ListItem>
            <ListItemText
              primary="No active alerts"
              secondary="All systems operating normally"
            />
          </ListItem>
        )}
      </List>
    </Paper>
  );
};

export default AlertsWidget;

// Made with Bob
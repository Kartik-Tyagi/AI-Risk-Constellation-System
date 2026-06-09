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
} from '@mui/material';
import { Close as CloseIcon, Settings as SettingsIcon } from '@mui/icons-material';
import { useRiskData } from '../../hooks/useRiskData';

const PortfolioWidget = ({ widgetId, title, onRemove, onSettings, settings }) => {
  const { data: portfolios, loading, error } = useRiskData('/portfolios');

  const getRiskColor = (level) => {
    switch (level?.toLowerCase()) {
      case 'low':
        return 'success';
      case 'medium':
        return 'warning';
      case 'high':
        return 'error';
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

      <List sx={{ flexGrow: 1, overflow: 'auto' }}>
        {portfolios?.slice(0, 5).map((portfolio, idx) => (
          <ListItem
            key={idx}
            secondaryAction={
              <Chip
                label={portfolio.risk_level || 'N/A'}
                color={getRiskColor(portfolio.risk_level)}
                size="small"
              />
            }
          >
            <ListItemText
              primary={portfolio.name || `Portfolio ${idx + 1}`}
              secondary={`Value: $${(portfolio.value || 0).toLocaleString()}`}
            />
          </ListItem>
        ))}
      </List>
    </Paper>
  );
};

export default PortfolioWidget;

// Made with Bob
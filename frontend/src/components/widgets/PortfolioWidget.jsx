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
import { portfolioApi } from '../../services/api';

const PortfolioWidget = ({ widgetId, title, onRemove, onSettings, settings }) => {
  const [portfolioList, setPortfolioList] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    portfolioApi.getAll()
      .then(res => setPortfolioList(res.data?.portfolios || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

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
        {portfolioList.slice(0, 5).map((portfolio, idx) => {
          const riskLevel = portfolio.metadata?.risk_level || portfolio.risk_level;
          return (
            <ListItem
              key={idx}
              secondaryAction={
                <Chip
                  label={riskLevel || 'N/A'}
                  color={getRiskColor(riskLevel)}
                  size="small"
                />
              }
            >
              <ListItemText
                primary={portfolio.name || `Portfolio ${idx + 1}`}
                secondary={`Value: $${(portfolio.total_value || 0).toLocaleString()}`}
              />
            </ListItem>
          );
        })}
      </List>
    </Paper>
  );
};

export default PortfolioWidget;

// Made with Bob
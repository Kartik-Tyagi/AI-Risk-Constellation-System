import React from 'react';
import {
  Paper,
  Typography,
  Box,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Tooltip,
  Chip,
} from '@mui/material';
import { Close as CloseIcon, Settings as SettingsIcon, OpenInNew as OpenInNewIcon } from '@mui/icons-material';
import { useRiskData } from '../../hooks/useRiskData';

const NewsWidget = ({ widgetId, title, onRemove, onSettings, settings }) => {
  const { data: news } = useRiskData('/risk/news');

  // Simulated news if no data
  const newsItems = news || [
    {
      title: 'Market Volatility Increases',
      summary: 'Risk levels elevated across financial sector',
      category: 'Market',
      timestamp: new Date().toISOString(),
    },
    {
      title: 'New Correlation Detected',
      summary: 'Strong correlation found between tech and energy sectors',
      category: 'Analysis',
      timestamp: new Date(Date.now() - 3600000).toISOString(),
    },
    {
      title: 'Risk Model Updated',
      summary: 'Improved prediction accuracy by 15%',
      category: 'System',
      timestamp: new Date(Date.now() - 7200000).toISOString(),
    },
  ];

  const getCategoryColor = (category) => {
    switch (category?.toLowerCase()) {
      case 'market':
        return 'primary';
      case 'analysis':
        return 'secondary';
      case 'system':
        return 'info';
      case 'alert':
        return 'warning';
      default:
        return 'default';
    }
  };

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
        {newsItems.map((item, idx) => (
          <ListItem
            key={idx}
            sx={{
              mb: 1,
              backgroundColor: 'background.default',
              borderRadius: 1,
            }}
            secondaryAction={
              <IconButton edge="end" size="small">
                <OpenInNewIcon fontSize="small" />
              </IconButton>
            }
          >
            <ListItemText
              primary={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                  <Typography variant="subtitle2">{item.title}</Typography>
                  <Chip label={item.category} color={getCategoryColor(item.category)} size="small" />
                </Box>
              }
              secondary={
                <>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                    {item.summary}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {new Date(item.timestamp).toLocaleString()}
                  </Typography>
                </>
              }
            />
          </ListItem>
        ))}
      </List>
    </Paper>
  );
};

export default NewsWidget;

// Made with Bob
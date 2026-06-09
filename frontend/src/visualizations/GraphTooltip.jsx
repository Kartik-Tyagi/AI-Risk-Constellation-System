import React from 'react';
import {
  Box,
  Paper,
  Typography,
  Divider,
  Chip,
  Stack,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Info,
  TrendingUp,
  AccountTree,
  Close,
} from '@mui/icons-material';

const GraphTooltip = ({ node, position, onClose, onViewDetails, onViewConnections }) => {
  if (!node) return null;

  const getRiskColor = (riskLevel) => {
    if (riskLevel >= 80) return 'error';
    if (riskLevel >= 60) return 'warning';
    if (riskLevel >= 40) return 'info';
    return 'success';
  };

  const formatValue = (value) => {
    if (!value) return 'N/A';
    if (value >= 1000000) return `$${(value / 1000000).toFixed(2)}M`;
    if (value >= 1000) return `$${(value / 1000).toFixed(2)}K`;
    return `$${value.toFixed(2)}`;
  };

  return (
    <Paper
      elevation={8}
      sx={{
        position: 'fixed',
        left: position?.x || 0,
        top: position?.y || 0,
        width: 280,
        maxWidth: '90vw',
        zIndex: 2000,
        pointerEvents: 'auto',
      }}
    >
      <Box sx={{ p: 2 }}>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h6" sx={{ fontSize: '1rem', fontWeight: 600 }}>
              {node.name}
            </Typography>
            {node.symbol && (
              <Typography variant="caption" color="text.secondary">
                {node.symbol}
              </Typography>
            )}
          </Box>
          <IconButton size="small" onClick={onClose}>
            <Close fontSize="small" />
          </IconButton>
        </Box>

        {/* Type and Sector */}
        <Stack direction="row" spacing={0.5} sx={{ mb: 2 }}>
          <Chip label={node.type} size="small" variant="outlined" />
          {node.sector && <Chip label={node.sector} size="small" variant="outlined" />}
        </Stack>

        <Divider sx={{ my: 1.5 }} />

        {/* Risk Metrics */}
        <Box sx={{ mb: 2 }}>
          <Typography variant="caption" color="text.secondary" gutterBottom>
            Risk Metrics
          </Typography>
          
          <Box sx={{ mt: 1 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
              <Typography variant="body2">Risk Level</Typography>
              <Chip
                label={`${node.riskLevel?.toFixed(1)}%`}
                size="small"
                color={getRiskColor(node.riskLevel)}
              />
            </Box>

            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
              <Typography variant="body2">Risk Score</Typography>
              <Typography variant="body2" fontWeight={600}>
                {node.riskScore?.toFixed(2)}
              </Typography>
            </Box>

            {node.value !== undefined && (
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Typography variant="body2">Value</Typography>
                <Typography variant="body2" fontWeight={600}>
                  {formatValue(node.value)}
                </Typography>
              </Box>
            )}
          </Box>
        </Box>

        {/* Additional Metadata */}
        {node.metadata && Object.keys(node.metadata).length > 0 && (
          <>
            <Divider sx={{ my: 1.5 }} />
            <Box sx={{ mb: 2 }}>
              <Typography variant="caption" color="text.secondary" gutterBottom>
                Additional Info
              </Typography>
              <Box sx={{ mt: 1 }}>
                {Object.entries(node.metadata).slice(0, 3).map(([key, value]) => (
                  <Box
                    key={key}
                    sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}
                  >
                    <Typography variant="caption" color="text.secondary">
                      {key}:
                    </Typography>
                    <Typography variant="caption">{String(value)}</Typography>
                  </Box>
                ))}
              </Box>
            </Box>
          </>
        )}

        <Divider sx={{ my: 1.5 }} />

        {/* Quick Actions */}
        <Stack direction="row" spacing={1}>
          <Tooltip title="View Details">
            <IconButton
              size="small"
              onClick={() => onViewDetails && onViewDetails(node)}
              sx={{ flex: 1 }}
            >
              <Info fontSize="small" />
            </IconButton>
          </Tooltip>

          <Tooltip title="View Connections">
            <IconButton
              size="small"
              onClick={() => onViewConnections && onViewConnections(node)}
              sx={{ flex: 1 }}
            >
              <AccountTree fontSize="small" />
            </IconButton>
          </Tooltip>

          <Tooltip title="Analyze Risk">
            <IconButton
              size="small"
              onClick={() => {
                // Handle risk analysis
              }}
              sx={{ flex: 1 }}
            >
              <TrendingUp fontSize="small" />
            </IconButton>
          </Tooltip>
        </Stack>
      </Box>
    </Paper>
  );
};

export default GraphTooltip;

// Made with Bob
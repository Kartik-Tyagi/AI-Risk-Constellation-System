import React from 'react';
import { Box, Paper, Typography, Stack, Divider } from '@mui/material';
import { getNodeColor, getNodeColorByType } from '../utils/graphUtils';

const GraphLegend = ({ colorScheme = 'risk', position = 'bottom-left' }) => {
  const getPositionStyles = () => {
    const base = {
      position: 'absolute',
      zIndex: 1000,
    };

    switch (position) {
      case 'top-left':
        return { ...base, top: 16, left: 16 };
      case 'top-right':
        return { ...base, top: 16, right: 16 };
      case 'bottom-left':
        return { ...base, bottom: 16, left: 16 };
      case 'bottom-right':
        return { ...base, bottom: 16, right: 16 };
      default:
        return { ...base, bottom: 16, left: 16 };
    }
  };

  const riskLevels = [
    { label: 'Critical', range: '80-100%', color: getNodeColor(90) },
    { label: 'High', range: '60-80%', color: getNodeColor(70) },
    { label: 'Medium', range: '40-60%', color: getNodeColor(50) },
    { label: 'Low', range: '20-40%', color: getNodeColor(30) },
    { label: 'Very Low', range: '0-20%', color: getNodeColor(10) },
  ];

  const entityTypes = [
    { label: 'Stock', type: 'stock' },
    { label: 'Bond', type: 'bond' },
    { label: 'Commodity', type: 'commodity' },
    { label: 'Currency', type: 'currency' },
    { label: 'Derivative', type: 'derivative' },
    { label: 'Fund', type: 'fund' },
    { label: 'Index', type: 'index' },
    { label: 'Sector', type: 'sector' },
    { label: 'Company', type: 'company' },
  ];

  const edgeTypes = [
    { label: 'Positive Risk', color: 'rgba(244, 67, 54, 0.8)', description: 'Increases risk' },
    { label: 'Negative Risk', color: 'rgba(76, 175, 80, 0.8)', description: 'Hedging effect' },
    { label: 'Neutral', color: 'rgba(158, 158, 158, 0.5)', description: 'No risk impact' },
  ];

  return (
    <Paper elevation={3} sx={{ ...getPositionStyles(), maxWidth: 250 }}>
      <Box sx={{ p: 2 }}>
        <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600 }}>
          Legend
        </Typography>

        <Divider sx={{ my: 1 }} />

        {/* Risk Level Legend */}
        {colorScheme === 'risk' && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="caption" color="text.secondary" gutterBottom>
              Risk Levels
            </Typography>
            <Stack spacing={0.5} sx={{ mt: 1 }}>
              {riskLevels.map((level) => (
                <Box key={level.label} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Box
                    sx={{
                      width: 16,
                      height: 16,
                      borderRadius: '50%',
                      backgroundColor: level.color,
                      border: '1px solid #fff',
                      flexShrink: 0,
                    }}
                  />
                  <Typography variant="caption">
                    {level.label}
                    <Typography
                      component="span"
                      variant="caption"
                      color="text.secondary"
                      sx={{ ml: 0.5 }}
                    >
                      ({level.range})
                    </Typography>
                  </Typography>
                </Box>
              ))}
            </Stack>
          </Box>
        )}

        {/* Entity Type Legend */}
        {colorScheme === 'type' && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="caption" color="text.secondary" gutterBottom>
              Entity Types
            </Typography>
            <Stack spacing={0.5} sx={{ mt: 1 }}>
              {entityTypes.map((entity) => (
                <Box key={entity.type} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Box
                    sx={{
                      width: 16,
                      height: 16,
                      borderRadius: '50%',
                      backgroundColor: getNodeColorByType(entity.type),
                      border: '1px solid #fff',
                      flexShrink: 0,
                    }}
                  />
                  <Typography variant="caption">{entity.label}</Typography>
                </Box>
              ))}
            </Stack>
          </Box>
        )}

        {/* Edge Types Legend */}
        <Box>
          <Typography variant="caption" color="text.secondary" gutterBottom>
            Connections
          </Typography>
          <Stack spacing={0.5} sx={{ mt: 1 }}>
            {edgeTypes.map((edge) => (
              <Box key={edge.label} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Box
                  sx={{
                    width: 20,
                    height: 3,
                    backgroundColor: edge.color,
                    flexShrink: 0,
                  }}
                />
                <Typography variant="caption">
                  {edge.label}
                  <Typography
                    component="span"
                    variant="caption"
                    color="text.secondary"
                    sx={{ ml: 0.5, fontSize: '0.65rem' }}
                  >
                    {edge.description}
                  </Typography>
                </Typography>
              </Box>
            ))}
          </Stack>
        </Box>

        {/* Node Size Legend */}
        <Box sx={{ mt: 2 }}>
          <Typography variant="caption" color="text.secondary" gutterBottom>
            Node Size
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
            <Box
              sx={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                backgroundColor: 'primary.main',
                border: '1px solid #fff',
              }}
            />
            <Typography variant="caption" sx={{ fontSize: '0.65rem' }}>
              Small
            </Typography>
            <Box
              sx={{
                width: 12,
                height: 12,
                borderRadius: '50%',
                backgroundColor: 'primary.main',
                border: '1px solid #fff',
              }}
            />
            <Typography variant="caption" sx={{ fontSize: '0.65rem' }}>
              Medium
            </Typography>
            <Box
              sx={{
                width: 16,
                height: 16,
                borderRadius: '50%',
                backgroundColor: 'primary.main',
                border: '1px solid #fff',
              }}
            />
            <Typography variant="caption" sx={{ fontSize: '0.65rem' }}>
              Large
            </Typography>
          </Box>
          <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.65rem', mt: 0.5 }}>
            Based on risk score, value, or connections
          </Typography>
        </Box>
      </Box>
    </Paper>
  );
};

export default GraphLegend;

// Made with Bob
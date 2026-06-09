import React from 'react';
import {
  Grid,
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Box,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  AccountBalance as PortfolioIcon,
  Warning as AlertIcon,
  BubbleChart as GraphIcon,
  ShowChart as ChartIcon,
  Speed as MetricsIcon,
  Article as NewsIcon,
} from '@mui/icons-material';

const WidgetLibrary = ({ onAddWidget }) => {
  const widgets = [
    {
      type: 'risk-summary',
      name: 'Risk Summary',
      description: 'Overview of overall risk metrics and trends',
      icon: <DashboardIcon sx={{ fontSize: 40 }} />,
      color: 'primary.main',
    },
    {
      type: 'portfolio',
      name: 'Portfolio Overview',
      description: 'List of portfolios with risk levels',
      icon: <PortfolioIcon sx={{ fontSize: 40 }} />,
      color: 'secondary.main',
    },
    {
      type: 'alerts',
      name: 'Risk Alerts',
      description: 'Real-time risk alerts and notifications',
      icon: <AlertIcon sx={{ fontSize: 40 }} />,
      color: 'warning.main',
    },
    {
      type: 'graph',
      name: 'Risk Network',
      description: 'Interactive risk network visualization',
      icon: <GraphIcon sx={{ fontSize: 40 }} />,
      color: 'info.main',
    },
    {
      type: 'chart',
      name: 'Risk Charts',
      description: 'Time series and distribution charts',
      icon: <ChartIcon sx={{ fontSize: 40 }} />,
      color: 'success.main',
    },
    {
      type: 'metrics',
      name: 'Key Metrics',
      description: 'Important risk metrics at a glance',
      icon: <MetricsIcon sx={{ fontSize: 40 }} />,
      color: 'error.main',
    },
    {
      type: 'news',
      name: 'Risk News',
      description: 'Latest risk-related news and updates',
      icon: <NewsIcon sx={{ fontSize: 40 }} />,
      color: 'text.secondary',
    },
  ];

  return (
    <Grid container spacing={2}>
      {widgets.map((widget) => (
        <Grid item xs={12} sm={6} md={4} key={widget.type}>
          <Card
            sx={{
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
              '&:hover': {
                boxShadow: 6,
                transform: 'translateY(-2px)',
                transition: 'all 0.2s',
              },
            }}
          >
            <CardContent sx={{ flexGrow: 1 }}>
              <Box
                sx={{
                  display: 'flex',
                  justifyContent: 'center',
                  mb: 2,
                  color: widget.color,
                }}
              >
                {widget.icon}
              </Box>
              <Typography variant="h6" gutterBottom align="center">
                {widget.name}
              </Typography>
              <Typography variant="body2" color="text.secondary" align="center">
                {widget.description}
              </Typography>
            </CardContent>
            <CardActions sx={{ justifyContent: 'center', pb: 2 }}>
              <Button
                variant="contained"
                onClick={() => onAddWidget(widget.type)}
                fullWidth
                sx={{ mx: 2 }}
              >
                Add Widget
              </Button>
            </CardActions>
          </Card>
        </Grid>
      ))}
    </Grid>
  );
};

export default WidgetLibrary;

// Made with Bob
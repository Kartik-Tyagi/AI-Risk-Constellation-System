import React, { useState, useEffect } from 'react';
import { Responsive, WidthProvider } from 'react-grid-layout';
import {
  Box,
  Button,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Typography,
  Paper,
} from '@mui/material';
import {
  Add as AddIcon,
  Settings as SettingsIcon,
  Save as SaveIcon,
  Restore as RestoreIcon,
  Lock as LockIcon,
  LockOpen as LockOpenIcon,
} from '@mui/icons-material';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';

// Import widgets
import RiskSummaryWidget from './widgets/RiskSummaryWidget';
import PortfolioWidget from './widgets/PortfolioWidget';
import AlertsWidget from './widgets/AlertsWidget';
import GraphWidget from './widgets/GraphWidget';
import ChartWidget from './widgets/ChartWidget';
import MetricsWidget from './widgets/MetricsWidget';
import NewsWidget from './widgets/NewsWidget';
import WidgetLibrary from './WidgetLibrary';
import dashboardService from '../services/dashboardService';

const ResponsiveGridLayout = WidthProvider(Responsive);

const Dashboard = () => {
  const [layouts, setLayouts] = useState({ lg: [] });
  const [widgets, setWidgets] = useState([]);
  const [isLocked, setIsLocked] = useState(false);
  const [showWidgetLibrary, setShowWidgetLibrary] = useState(false);
  const [selectedWidget, setSelectedWidget] = useState(null);
  const [widgetSettings, setWidgetSettings] = useState({});

  // Load saved dashboard on mount
  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    const savedDashboard = await dashboardService.loadDashboard('default');
    if (savedDashboard) {
      setLayouts(savedDashboard.layouts);
      setWidgets(savedDashboard.widgets);
      setWidgetSettings(savedDashboard.settings || {});
    } else {
      // Load default dashboard
      loadDefaultDashboard();
    }
  };

  const loadDefaultDashboard = () => {
    const defaultWidgets = [
      {
        i: 'risk-summary-1',
        type: 'risk-summary',
        title: 'Risk Summary',
      },
      {
        i: 'portfolio-1',
        type: 'portfolio',
        title: 'Portfolio Overview',
      },
      {
        i: 'alerts-1',
        type: 'alerts',
        title: 'Risk Alerts',
      },
      {
        i: 'graph-1',
        type: 'graph',
        title: 'Risk Network',
      },
    ];

    const defaultLayout = [
      { i: 'risk-summary-1', x: 0, y: 0, w: 6, h: 2 },
      { i: 'portfolio-1', x: 6, y: 0, w: 6, h: 2 },
      { i: 'alerts-1', x: 0, y: 2, w: 4, h: 3 },
      { i: 'graph-1', x: 4, y: 2, w: 8, h: 3 },
    ];

    setWidgets(defaultWidgets);
    setLayouts({ lg: defaultLayout });
  };

  const saveDashboard = async () => {
    await dashboardService.saveDashboard('default', {
      layouts,
      widgets,
      settings: widgetSettings,
    });
  };

  const resetDashboard = () => {
    loadDefaultDashboard();
  };

  const handleLayoutChange = (layout, layouts) => {
    setLayouts(layouts);
  };

  const handleAddWidget = (widgetType) => {
    const newWidget = {
      i: `${widgetType}-${Date.now()}`,
      type: widgetType,
      title: getWidgetTitle(widgetType),
    };

    const newLayout = {
      i: newWidget.i,
      x: (widgets.length * 3) % 12,
      y: Infinity, // Put at bottom
      w: 4,
      h: 2,
    };

    setWidgets([...widgets, newWidget]);
    setLayouts({
      ...layouts,
      lg: [...(layouts.lg || []), newLayout],
    });
    setShowWidgetLibrary(false);
  };

  const handleRemoveWidget = (widgetId) => {
    setWidgets(widgets.filter((w) => w.i !== widgetId));
    setLayouts({
      ...layouts,
      lg: (layouts.lg || []).filter((l) => l.i !== widgetId),
    });
  };

  const handleWidgetSettings = (widgetId, settings) => {
    setWidgetSettings({
      ...widgetSettings,
      [widgetId]: settings,
    });
  };

  const getWidgetTitle = (type) => {
    const titles = {
      'risk-summary': 'Risk Summary',
      portfolio: 'Portfolio Overview',
      alerts: 'Risk Alerts',
      graph: 'Risk Network',
      chart: 'Risk Chart',
      metrics: 'Key Metrics',
      news: 'Risk News',
    };
    return titles[type] || 'Widget';
  };

  const renderWidget = (widget) => {
    const settings = widgetSettings[widget.i] || {};
    const commonProps = {
      widgetId: widget.i,
      title: widget.title,
      onRemove: () => handleRemoveWidget(widget.i),
      onSettings: (s) => handleWidgetSettings(widget.i, s),
      settings,
    };

    switch (widget.type) {
      case 'risk-summary':
        return <RiskSummaryWidget {...commonProps} />;
      case 'portfolio':
        return <PortfolioWidget {...commonProps} />;
      case 'alerts':
        return <AlertsWidget {...commonProps} />;
      case 'graph':
        return <GraphWidget {...commonProps} />;
      case 'chart':
        return <ChartWidget {...commonProps} />;
      case 'metrics':
        return <MetricsWidget {...commonProps} />;
      case 'news':
        return <NewsWidget {...commonProps} />;
      default:
        return (
          <Paper sx={{ p: 2, height: '100%' }}>
            <Typography>Unknown widget type: {widget.type}</Typography>
          </Paper>
        );
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Dashboard Header */}
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          mb: 3,
        }}
      >
        <Typography variant="h4">Dashboard</Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="Add Widget">
            <IconButton onClick={() => setShowWidgetLibrary(true)} color="primary">
              <AddIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title={isLocked ? 'Unlock Layout' : 'Lock Layout'}>
            <IconButton onClick={() => setIsLocked(!isLocked)} color={isLocked ? 'error' : 'default'}>
              {isLocked ? <LockIcon /> : <LockOpenIcon />}
            </IconButton>
          </Tooltip>
          <Tooltip title="Save Dashboard">
            <IconButton onClick={saveDashboard} color="primary">
              <SaveIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Reset to Default">
            <IconButton onClick={resetDashboard}>
              <RestoreIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Grid Layout */}
      <ResponsiveGridLayout
        className="layout"
        layouts={layouts}
        breakpoints={{ lg: 1200, md: 996, sm: 768, xs: 480, xxs: 0 }}
        cols={{ lg: 12, md: 10, sm: 6, xs: 4, xxs: 2 }}
        rowHeight={100}
        onLayoutChange={handleLayoutChange}
        isDraggable={!isLocked}
        isResizable={!isLocked}
        compactType="vertical"
        preventCollision={false}
      >
        {widgets.map((widget) => (
          <div key={widget.i}>
            {renderWidget(widget)}
          </div>
        ))}
      </ResponsiveGridLayout>

      {/* Widget Library Dialog */}
      <Dialog
        open={showWidgetLibrary}
        onClose={() => setShowWidgetLibrary(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Add Widget</DialogTitle>
        <DialogContent>
          <WidgetLibrary onAddWidget={handleAddWidget} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowWidgetLibrary(false)}>Cancel</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Dashboard;

// Made with Bob
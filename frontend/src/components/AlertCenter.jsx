import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Chip,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Tabs,
  Tab,
  Badge,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  CheckCircle as CheckCircleIcon,
  Close as CloseIcon,
  FilterList as FilterIcon,
  Refresh as RefreshIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { useWebSocket } from '../hooks/useWebSocket';
import alertService from '../services/alertService';

const AlertCenter = () => {
  const [alerts, setAlerts] = useState([]);
  const [filteredAlerts, setFilteredAlerts] = useState([]);
  const [activeTab, setActiveTab] = useState(0); // 0: Active, 1: Acknowledged, 2: All
  const [severityFilter, setSeverityFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [showDetails, setShowDetails] = useState(false);

  // WebSocket connection for real-time alerts
  const { lastMessage } = useWebSocket('/ws/alerts');

  // Load alerts on mount
  useEffect(() => {
    loadAlerts();
  }, []);

  // Handle incoming WebSocket messages
  useEffect(() => {
    if (lastMessage) {
      try {
        const alert = JSON.parse(lastMessage.data);
        handleNewAlert(alert);
      } catch (error) {
        console.error('Error parsing alert:', error);
      }
    }
  }, [lastMessage]);

  // Apply filters
  useEffect(() => {
    applyFilters();
  }, [alerts, activeTab, severityFilter, typeFilter, searchQuery]);

  const loadAlerts = async () => {
    const loadedAlerts = await alertService.getAlerts();
    setAlerts(loadedAlerts);
  };

  const handleNewAlert = (alert) => {
    setAlerts((prev) => [alert, ...prev]);
    // Show toast notification
    alertService.showToast(alert);
  };

  const applyFilters = () => {
    let filtered = [...alerts];

    // Tab filter (active/acknowledged/all)
    if (activeTab === 0) {
      filtered = filtered.filter((a) => !a.acknowledged);
    } else if (activeTab === 1) {
      filtered = filtered.filter((a) => a.acknowledged);
    }

    // Severity filter
    if (severityFilter !== 'all') {
      filtered = filtered.filter((a) => a.severity === severityFilter);
    }

    // Type filter
    if (typeFilter !== 'all') {
      filtered = filtered.filter((a) => a.type === typeFilter);
    }

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (a) =>
          a.message.toLowerCase().includes(query) ||
          a.entity_id?.toLowerCase().includes(query)
      );
    }

    setFilteredAlerts(filtered);
  };

  const handleAcknowledge = async (alertId) => {
    await alertService.acknowledgeAlert(alertId);
    setAlerts((prev) =>
      prev.map((a) => (a.id === alertId ? { ...a, acknowledged: true } : a))
    );
  };

  const handleDismiss = async (alertId) => {
    await alertService.dismissAlert(alertId);
    setAlerts((prev) => prev.filter((a) => a.id !== alertId));
  };

  const handleClearAll = async () => {
    await alertService.clearAllAlerts();
    setAlerts([]);
  };

  const handleShowDetails = (alert) => {
    setSelectedAlert(alert);
    setShowDetails(true);
  };

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

  const getAlertTypeLabel = (type) => {
    const labels = {
      threshold_breach: 'Threshold Breach',
      cascade_detected: 'Cascade Detected',
      anomaly_detected: 'Anomaly Detected',
      model_prediction: 'Model Prediction',
    };
    return labels[type] || type;
  };

  const activeCount = alerts.filter((a) => !a.acknowledged).length;
  const acknowledgedCount = alerts.filter((a) => a.acknowledged).length;

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Alert Center</Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="Refresh">
            <IconButton onClick={loadAlerts}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Clear All">
            <IconButton onClick={handleClearAll} color="error">
              <DeleteIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Tabs */}
      <Paper sx={{ mb: 2 }}>
        <Tabs value={activeTab} onChange={(e, v) => setActiveTab(v)}>
          <Tab
            label={
              <Badge badgeContent={activeCount} color="error">
                Active
              </Badge>
            }
          />
          <Tab
            label={
              <Badge badgeContent={acknowledgedCount} color="success">
                Acknowledged
              </Badge>
            }
          />
          <Tab label="All" />
        </Tabs>
      </Paper>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <TextField
            label="Search"
            variant="outlined"
            size="small"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            sx={{ flexGrow: 1, minWidth: 200 }}
          />
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Severity</InputLabel>
            <Select
              value={severityFilter}
              label="Severity"
              onChange={(e) => setSeverityFilter(e.target.value)}
            >
              <MenuItem value="all">All</MenuItem>
              <MenuItem value="critical">Critical</MenuItem>
              <MenuItem value="warning">Warning</MenuItem>
              <MenuItem value="info">Info</MenuItem>
            </Select>
          </FormControl>
          <FormControl size="small" sx={{ minWidth: 200 }}>
            <InputLabel>Type</InputLabel>
            <Select
              value={typeFilter}
              label="Type"
              onChange={(e) => setTypeFilter(e.target.value)}
            >
              <MenuItem value="all">All</MenuItem>
              <MenuItem value="threshold_breach">Threshold Breach</MenuItem>
              <MenuItem value="cascade_detected">Cascade Detected</MenuItem>
              <MenuItem value="anomaly_detected">Anomaly Detected</MenuItem>
              <MenuItem value="model_prediction">Model Prediction</MenuItem>
            </Select>
          </FormControl>
        </Box>
      </Paper>

      {/* Alert List */}
      <Paper>
        <List>
          {filteredAlerts.length === 0 ? (
            <ListItem>
              <ListItemText
                primary="No alerts"
                secondary="All systems operating normally"
              />
            </ListItem>
          ) : (
            filteredAlerts.map((alert) => (
              <ListItem
                key={alert.id}
                sx={{
                  borderLeft: 4,
                  borderColor: `${getSeverityColor(alert.severity)}.main`,
                  mb: 1,
                  backgroundColor: alert.acknowledged ? 'action.hover' : 'background.paper',
                }}
                secondaryAction={
                  <Box>
                    {!alert.acknowledged && (
                      <Tooltip title="Acknowledge">
                        <IconButton
                          edge="end"
                          onClick={() => handleAcknowledge(alert.id)}
                          color="success"
                        >
                          <CheckCircleIcon />
                        </IconButton>
                      </Tooltip>
                    )}
                    <Tooltip title="Dismiss">
                      <IconButton edge="end" onClick={() => handleDismiss(alert.id)}>
                        <CloseIcon />
                      </IconButton>
                    </Tooltip>
                  </Box>
                }
              >
                <ListItemIcon>{getSeverityIcon(alert.severity)}</ListItemIcon>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                      <Typography variant="subtitle1">{alert.message}</Typography>
                      <Chip
                        label={alert.severity}
                        color={getSeverityColor(alert.severity)}
                        size="small"
                      />
                      <Chip label={getAlertTypeLabel(alert.type)} size="small" variant="outlined" />
                    </Box>
                  }
                  secondary={
                    <Box>
                      {alert.entity_id && (
                        <Typography variant="body2" color="text.secondary">
                          Entity: {alert.entity_id}
                        </Typography>
                      )}
                      <Typography variant="caption" color="text.secondary">
                        {new Date(alert.timestamp).toLocaleString()}
                      </Typography>
                      {alert.details && (
                        <Button size="small" onClick={() => handleShowDetails(alert)} sx={{ ml: 1 }}>
                          Details
                        </Button>
                      )}
                    </Box>
                  }
                />
              </ListItem>
            ))
          )}
        </List>
      </Paper>

      {/* Alert Details Dialog */}
      <Dialog open={showDetails} onClose={() => setShowDetails(false)} maxWidth="md" fullWidth>
        <DialogTitle>Alert Details</DialogTitle>
        <DialogContent>
          {selectedAlert && (
            <Box>
              <Typography variant="h6" gutterBottom>
                {selectedAlert.message}
              </Typography>
              <Box sx={{ mb: 2 }}>
                <Chip
                  label={selectedAlert.severity}
                  color={getSeverityColor(selectedAlert.severity)}
                  sx={{ mr: 1 }}
                />
                <Chip label={getAlertTypeLabel(selectedAlert.type)} variant="outlined" />
              </Box>
              {selectedAlert.entity_id && (
                <Typography variant="body1" gutterBottom>
                  <strong>Entity:</strong> {selectedAlert.entity_id}
                </Typography>
              )}
              <Typography variant="body1" gutterBottom>
                <strong>Timestamp:</strong> {new Date(selectedAlert.timestamp).toLocaleString()}
              </Typography>
              {selectedAlert.details && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Additional Details:
                  </Typography>
                  <Paper sx={{ p: 2, backgroundColor: 'background.default' }}>
                    <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                      {JSON.stringify(selectedAlert.details, null, 2)}
                    </pre>
                  </Paper>
                </Box>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          {selectedAlert && !selectedAlert.acknowledged && (
            <Button
              onClick={() => {
                handleAcknowledge(selectedAlert.id);
                setShowDetails(false);
              }}
              color="success"
            >
              Acknowledge
            </Button>
          )}
          <Button onClick={() => setShowDetails(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AlertCenter;

// Made with Bob
import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Box,
  Chip,
  Tooltip,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Notifications as NotificationsIcon,
  WifiOff as DisconnectedIcon,
  Wifi as ConnectedIcon,
} from '@mui/icons-material';
import { useApp } from '../../context/AppContext';
import { useWebSocket } from '../../hooks/useWebSocket';

const Header = () => {
  const { toggleSidebar, systemHealth } = useApp();
  const { isConnected } = useWebSocket();

  const getHealthColor = () => {
    if (!systemHealth) return 'default';
    switch (systemHealth.status) {
      case 'healthy':
        return 'success';
      case 'degraded':
        return 'warning';
      case 'unhealthy':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <AppBar
      position="static"
      elevation={0}
      sx={{
        backgroundColor: 'background.paper',
        borderBottom: '1px solid',
        borderColor: 'divider',
      }}
    >
      <Toolbar>
        <IconButton
          edge="start"
          color="inherit"
          aria-label="menu"
          onClick={toggleSidebar}
          sx={{ mr: 2 }}
        >
          <MenuIcon />
        </IconButton>

        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          {/* Page title will be set by individual routes */}
        </Typography>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          {/* WebSocket Connection Status */}
          <Tooltip title={isConnected ? 'Connected' : 'Disconnected'}>
            <Chip
              icon={isConnected ? <ConnectedIcon /> : <DisconnectedIcon />}
              label={isConnected ? 'Live' : 'Offline'}
              color={isConnected ? 'success' : 'error'}
              size="small"
              variant="outlined"
            />
          </Tooltip>

          {/* System Health Status */}
          {systemHealth && (
            <Tooltip title={`System: ${systemHealth.status}`}>
              <Chip
                label="System"
                color={getHealthColor()}
                size="small"
                variant="outlined"
              />
            </Tooltip>
          )}

          {/* Notifications */}
          <IconButton color="inherit">
            <NotificationsIcon />
          </IconButton>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Header;

// Made with Bob
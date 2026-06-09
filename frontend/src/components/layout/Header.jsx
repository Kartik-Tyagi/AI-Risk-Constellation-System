import React from 'react';
import { useLocation } from 'react-router-dom';
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
  MenuOpen as MenuOpenIcon,
  WifiOff as DisconnectedIcon,
  Wifi as ConnectedIcon,
  FiberManualRecord as DotIcon,
} from '@mui/icons-material';
import { useApp } from '../../context/AppContext';
import { useWebSocket } from '../../hooks/useWebSocket';

const PAGE_TITLES = {
  '/dashboard': 'Dashboard',
  '/constellation': 'Risk Constellation',
  '/portfolio': 'Portfolio Analysis',
  '/settings': 'Settings',
};

const Header = () => {
  const { toggleSidebar, sidebarOpen, systemHealth } = useApp();
  const { isConnected } = useWebSocket();
  const location = useLocation();

  const pageTitle = PAGE_TITLES[location.pathname] || 'Risk Constellation';

  const healthColor = !systemHealth
    ? 'text.disabled'
    : systemHealth.status === 'healthy'
    ? 'success.main'
    : systemHealth.status === 'degraded'
    ? 'warning.main'
    : 'error.main';

  return (
    <AppBar
      position="static"
      elevation={0}
      sx={{
        backgroundColor: 'background.paper',
        borderBottom: '1px solid',
        borderColor: 'divider',
        zIndex: 10,
      }}
    >
      <Toolbar variant="dense" sx={{ minHeight: 48, px: 1.5 }}>
        {/* Sidebar toggle */}
        <Tooltip title={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}>
          <IconButton
            size="small"
            color="inherit"
            onClick={toggleSidebar}
            sx={{ mr: 1.5, color: 'text.secondary' }}
          >
            {sidebarOpen ? <MenuOpenIcon fontSize="small" /> : <MenuIcon fontSize="small" />}
          </IconButton>
        </Tooltip>

        {/* Page title */}
        <Typography variant="subtitle1" sx={{ fontWeight: 600, flexGrow: 1 }}>
          {pageTitle}
        </Typography>

        {/* Status indicators */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          {/* System health dot */}
          {systemHealth && (
            <Tooltip title={`System ${systemHealth.status}`}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                <DotIcon sx={{ fontSize: 10, color: healthColor }} />
                <Typography variant="caption" color="text.secondary">
                  {systemHealth.status}
                </Typography>
              </Box>
            </Tooltip>
          )}

          {/* Live / Offline chip */}
          <Tooltip title={isConnected ? 'Real-time connected' : 'Disconnected'}>
            <Chip
              icon={isConnected ? <ConnectedIcon /> : <DisconnectedIcon />}
              label={isConnected ? 'Live' : 'Offline'}
              color={isConnected ? 'success' : 'default'}
              size="small"
              variant="outlined"
              sx={{ height: 24, fontSize: '0.7rem' }}
            />
          </Tooltip>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Header;

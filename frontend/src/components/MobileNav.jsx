import React, { useState } from 'react';
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  IconButton,
  Box,
  Divider,
  Typography,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Close as CloseIcon,
  Dashboard as DashboardIcon,
  BubbleChart as GraphIcon,
  AccountBalance as PortfolioIcon,
  Assessment as AnalysisIcon,
  Notifications as AlertsIcon,
  Settings as SettingsIcon,
  Help as HelpIcon,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';

const MobileNav = () => {
  const [open, setOpen] = useState(false);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
    { text: 'Risk Constellation', icon: <GraphIcon />, path: '/constellation' },
    { text: 'Portfolio Analysis', icon: <PortfolioIcon />, path: '/portfolio' },
    { text: 'Analysis', icon: <AnalysisIcon />, path: '/analysis' },
    { text: 'Alerts', icon: <AlertsIcon />, path: '/alerts' },
    { text: 'Settings', icon: <SettingsIcon />, path: '/settings' },
    { text: 'Help', icon: <HelpIcon />, path: '/help' },
  ];

  const handleToggle = () => {
    setOpen(!open);
  };

  const handleNavigate = (path) => {
    navigate(path);
    setOpen(false);
  };

  if (!isMobile) {
    return null; // Don't render on desktop
  }

  return (
    <>
      {/* Hamburger Menu Button */}
      <IconButton
        edge="start"
        color="inherit"
        aria-label="menu"
        onClick={handleToggle}
        sx={{
          position: 'fixed',
          top: 16,
          left: 16,
          zIndex: theme.zIndex.drawer + 2,
          backgroundColor: 'primary.main',
          color: 'white',
          '&:hover': {
            backgroundColor: 'primary.dark',
          },
        }}
      >
        {open ? <CloseIcon /> : <MenuIcon />}
      </IconButton>

      {/* Drawer */}
      <Drawer
        anchor="left"
        open={open}
        onClose={() => setOpen(false)}
        sx={{
          '& .MuiDrawer-paper': {
            width: 280,
            boxSizing: 'border-box',
          },
        }}
      >
        {/* Header */}
        <Box
          sx={{
            p: 2,
            backgroundColor: 'primary.main',
            color: 'white',
          }}
        >
          <Typography variant="h6" noWrap>
            AI Risk System
          </Typography>
          <Typography variant="caption">
            Risk Constellation Analysis
          </Typography>
        </Box>

        <Divider />

        {/* Menu Items */}
        <List>
          {menuItems.map((item) => (
            <ListItem key={item.text} disablePadding>
              <ListItemButton
                selected={location.pathname === item.path}
                onClick={() => handleNavigate(item.path)}
                sx={{
                  '&.Mui-selected': {
                    backgroundColor: 'primary.light',
                    '&:hover': {
                      backgroundColor: 'primary.light',
                    },
                  },
                }}
              >
                <ListItemIcon
                  sx={{
                    color: location.pathname === item.path ? 'primary.main' : 'inherit',
                  }}
                >
                  {item.icon}
                </ListItemIcon>
                <ListItemText primary={item.text} />
              </ListItemButton>
            </ListItem>
          ))}
        </List>

        <Divider />

        {/* Footer */}
        <Box
          sx={{
            p: 2,
            mt: 'auto',
            textAlign: 'center',
          }}
        >
          <Typography variant="caption" color="text.secondary">
            Version 1.0.0
          </Typography>
        </Box>
      </Drawer>
    </>
  );
};

export default MobileNav;

// Made with Bob
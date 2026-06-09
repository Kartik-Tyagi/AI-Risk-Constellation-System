import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Box,
  Typography,
  Divider,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  BubbleChart as ConstellationIcon,
  Assessment as PortfolioIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import { useApp } from '../../context/AppContext';

const DRAWER_WIDTH = 240;

const menuItems = [
  { path: '/dashboard', label: 'Dashboard', icon: <DashboardIcon /> },
  { path: '/constellation', label: 'Risk Constellation', icon: <ConstellationIcon /> },
  { path: '/portfolio', label: 'Portfolio Analysis', icon: <PortfolioIcon /> },
  { path: '/settings', label: 'Settings', icon: <SettingsIcon /> },
];

const Navigation = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { sidebarOpen } = useApp();

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: sidebarOpen ? DRAWER_WIDTH : 0,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: DRAWER_WIDTH,
          boxSizing: 'border-box',
          backgroundColor: 'background.paper',
          borderRight: '1px solid',
          borderColor: 'divider',
        },
      }}
    >
      <Box sx={{ p: 3 }}>
        <Typography variant="h5" component="div" sx={{ fontWeight: 600 }}>
          Risk Constellation
        </Typography>
        <Typography variant="caption" color="text.secondary">
          AI-Powered Risk Analysis
        </Typography>
      </Box>
      
      <Divider />
      
      <List sx={{ px: 1, py: 2 }}>
        {menuItems.map((item) => (
          <ListItem key={item.path} disablePadding sx={{ mb: 0.5 }}>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => navigate(item.path)}
              sx={{
                borderRadius: 1,
                '&.Mui-selected': {
                  backgroundColor: 'primary.main',
                  color: 'primary.contrastText',
                  '&:hover': {
                    backgroundColor: 'primary.dark',
                  },
                  '& .MuiListItemIcon-root': {
                    color: 'primary.contrastText',
                  },
                },
              }}
            >
              <ListItemIcon
                sx={{
                  minWidth: 40,
                  color: location.pathname === item.path ? 'inherit' : 'text.secondary',
                }}
              >
                {item.icon}
              </ListItemIcon>
              <ListItemText primary={item.label} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Drawer>
  );
};

export default Navigation;

// Made with Bob
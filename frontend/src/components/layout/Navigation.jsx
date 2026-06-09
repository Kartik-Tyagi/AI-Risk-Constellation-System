import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
  Divider,
  Tooltip,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  BubbleChart as ConstellationIcon,
  Assessment as PortfolioIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import { useApp } from '../../context/AppContext';

const DRAWER_WIDTH = 220;
const RAIL_WIDTH = 56;

const menuItems = [
  { path: '/dashboard', label: 'Dashboard', icon: <DashboardIcon fontSize="small" /> },
  { path: '/constellation', label: 'Risk Constellation', icon: <ConstellationIcon fontSize="small" /> },
  { path: '/portfolio', label: 'Portfolio Analysis', icon: <PortfolioIcon fontSize="small" /> },
  { path: '/settings', label: 'Settings', icon: <SettingsIcon fontSize="small" /> },
];

const Navigation = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { sidebarOpen } = useApp();

  const width = sidebarOpen ? DRAWER_WIDTH : RAIL_WIDTH;

  return (
    <Box
      sx={{
        width,
        flexShrink: 0,
        height: '100vh',
        backgroundColor: 'background.paper',
        borderRight: '1px solid',
        borderColor: 'divider',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        transition: 'width 200ms ease',
      }}
    >
      {/* Logo area */}
      <Box
        sx={{
          height: 48,
          display: 'flex',
          alignItems: 'center',
          px: sidebarOpen ? 2 : 0,
          justifyContent: sidebarOpen ? 'flex-start' : 'center',
          flexShrink: 0,
          borderBottom: '1px solid',
          borderColor: 'divider',
        }}
      >
        <BubbleChart sx={{ color: 'primary.main', fontSize: 20 }} />
        {sidebarOpen && (
          <Box sx={{ ml: 1.5, overflow: 'hidden' }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 700, lineHeight: 1.2, whiteSpace: 'nowrap' }}>
              Risk Constellation
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ whiteSpace: 'nowrap' }}>
              AI Risk Analysis
            </Typography>
          </Box>
        )}
      </Box>

      {/* Nav items */}
      <List sx={{ px: sidebarOpen ? 1 : 0.5, py: 1, flexGrow: 1 }}>
        {menuItems.map((item) => {
          const active = location.pathname === item.path;
          const btn = (
            <ListItemButton
              selected={active}
              onClick={() => navigate(item.path)}
              sx={{
                borderRadius: 1,
                minHeight: 40,
                justifyContent: sidebarOpen ? 'flex-start' : 'center',
                px: sidebarOpen ? 1.5 : 1,
                '&.Mui-selected': {
                  backgroundColor: 'primary.main',
                  color: 'primary.contrastText',
                  '&:hover': { backgroundColor: 'primary.dark' },
                  '& .MuiListItemIcon-root': { color: 'primary.contrastText' },
                },
              }}
            >
              <ListItemIcon
                sx={{
                  minWidth: sidebarOpen ? 36 : 'auto',
                  color: active ? 'inherit' : 'text.secondary',
                  justifyContent: 'center',
                }}
              >
                {item.icon}
              </ListItemIcon>
              {sidebarOpen && (
                <ListItemText
                  primary={item.label}
                  primaryTypographyProps={{ variant: 'body2', noWrap: true }}
                />
              )}
            </ListItemButton>
          );

          return (
            <ListItem key={item.path} disablePadding sx={{ mb: 0.25, display: 'block' }}>
              {sidebarOpen ? btn : (
                <Tooltip title={item.label} placement="right">
                  {btn}
                </Tooltip>
              )}
            </ListItem>
          );
        })}
      </List>
    </Box>
  );
};

// Inline icon to avoid extra import
const BubbleChart = (props) => (
  <svg viewBox="0 0 24 24" width="1em" height="1em" fill="currentColor" style={{ fontSize: props.sx?.fontSize || 24 }}>
    <path d="M7 10c-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4-1.79-4-4-4zm0 6c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm8.01-7c1.65 0 2.99-1.34 2.99-3S16.66 3 15.01 3C13.36 3 12 4.34 12 6s1.36 3 3.01 3zm0-4c.55 0 .99.45.99 1s-.44 1-.99 1c-.56 0-1.01-.45-1.01-1s.45-1 1.01-1zM18 14.5c0 1.38 1.12 2.5 2.5 2.5S23 15.88 23 14.5 21.88 12 20.5 12 18 13.12 18 14.5zm3 0c0 .28-.22.5-.5.5s-.5-.22-.5-.5.22-.5.5-.5.5.22.5.5z" />
  </svg>
);

export default Navigation;

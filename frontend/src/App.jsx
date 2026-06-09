import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import { Box } from '@mui/material';

import { AppProvider } from './context/AppContext';
import { RiskProvider } from './context/RiskContext';
import { UserProvider } from './context/UserContext';

import Navigation from './components/layout/Navigation';
import Header from './components/layout/Header';

import Dashboard from './routes/Dashboard';
import RiskConstellation from './routes/RiskConstellation';
import PortfolioAnalysis from './routes/PortfolioAnalysis';
import Settings from './routes/Settings';

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#00bcd4',
      light: '#62efff',
      dark: '#008ba3',
    },
    secondary: {
      main: '#ff4081',
      light: '#ff79b0',
      dark: '#c60055',
    },
    error:   { main: '#f44336' },
    warning: { main: '#ff9800' },
    success: { main: '#4caf50' },
    background: {
      default: '#0a0e27',
      paper:   '#131829',
    },
    text: {
      primary:   '#e8eaf6',
      secondary: '#8c9ab0',
    },
    divider: 'rgba(255,255,255,0.07)',
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    fontSize: 13,
    h4: { fontSize: '1.35rem', fontWeight: 600 },
    h5: { fontSize: '1.1rem',  fontWeight: 600 },
    h6: { fontSize: '0.95rem', fontWeight: 600 },
    subtitle1: { fontSize: '0.9rem', fontWeight: 500 },
    subtitle2: { fontSize: '0.82rem', fontWeight: 600 },
    body1:   { fontSize: '0.875rem' },
    body2:   { fontSize: '0.8rem' },
    caption: { fontSize: '0.72rem' },
  },
  shape: { borderRadius: 6 },
  spacing: 8,
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        html: { height: '100%' },
        body: { height: '100%', overflow: 'hidden' },
        '#root': { height: '100%' },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          backgroundColor: '#1a2035',
          border: '1px solid rgba(255,255,255,0.06)',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          backgroundColor: '#131829',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: { backgroundImage: 'none' },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: { textTransform: 'none', fontWeight: 500 },
        sizeSmall: { fontSize: '0.78rem' },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: { fontSize: '0.72rem' },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: { fontSize: '0.8rem', padding: '6px 12px' },
        head: { fontWeight: 600, color: '#8c9ab0' },
      },
    },
    MuiTooltip: {
      styleOverrides: {
        tooltip: { fontSize: '0.72rem' },
      },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: { paddingTop: 6, paddingBottom: 6 },
      },
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <UserProvider>
        <AppProvider>
          <RiskProvider>
            <Router>
              <Box sx={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
                {/* Collapsible sidebar — always rendered, slides to icon rail */}
                <Navigation />

                {/* Main content column */}
                <Box
                  component="main"
                  sx={{
                    flexGrow: 1,
                    display: 'flex',
                    flexDirection: 'column',
                    minWidth: 0,
                    height: '100vh',
                    overflow: 'hidden',
                  }}
                >
                  <Header />

                  {/* Scrollable page body */}
                  <Box
                    sx={{
                      flexGrow: 1,
                      overflow: 'auto',
                      backgroundColor: 'background.default',
                    }}
                  >
                    <Routes>
                      <Route path="/" element={<Navigate to="/dashboard" replace />} />
                      <Route path="/dashboard"    element={<Dashboard />} />
                      <Route path="/constellation" element={<RiskConstellation />} />
                      <Route path="/portfolio"     element={<PortfolioAnalysis />} />
                      <Route path="/settings"      element={<Settings />} />
                      <Route path="*" element={<Navigate to="/dashboard" replace />} />
                    </Routes>
                  </Box>
                </Box>
              </Box>
            </Router>
          </RiskProvider>
        </AppProvider>
      </UserProvider>
    </ThemeProvider>
  );
}

export default App;

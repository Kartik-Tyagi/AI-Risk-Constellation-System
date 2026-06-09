import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import { Box } from '@mui/material';

// Context Providers
import { AppProvider } from './context/AppContext';
import { RiskProvider } from './context/RiskContext';
import { UserProvider } from './context/UserContext';

// Layout Components
import Navigation from './components/layout/Navigation';
import Header from './components/layout/Header';

// Route Components
import Dashboard from './routes/Dashboard';
import RiskConstellation from './routes/RiskConstellation';
import PortfolioAnalysis from './routes/PortfolioAnalysis';
import Settings from './routes/Settings';

// Create dark theme for risk visualization
const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#00bcd4', // Cyan for primary actions
      light: '#62efff',
      dark: '#008ba3',
    },
    secondary: {
      main: '#ff4081', // Pink for secondary actions
      light: '#ff79b0',
      dark: '#c60055',
    },
    error: {
      main: '#f44336',
    },
    warning: {
      main: '#ff9800',
    },
    success: {
      main: '#4caf50',
    },
    background: {
      default: '#0a0e27',
      paper: '#1a1f3a',
    },
    text: {
      primary: '#ffffff',
      secondary: '#b0bec5',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 500,
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 500,
    },
    h3: {
      fontSize: '1.75rem',
      fontWeight: 500,
    },
    h4: {
      fontSize: '1.5rem',
      fontWeight: 500,
    },
    h5: {
      fontSize: '1.25rem',
      fontWeight: 500,
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 500,
    },
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          backgroundColor: '#1a1f3a',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
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
              <Box sx={{ display: 'flex', minHeight: '100vh' }}>
                {/* Side Navigation */}
                <Navigation />
                
                {/* Main Content Area */}
                <Box
                  component="main"
                  sx={{
                    flexGrow: 1,
                    display: 'flex',
                    flexDirection: 'column',
                    overflow: 'hidden',
                  }}
                >
                  {/* Top Header */}
                  <Header />
                  
                  {/* Page Content */}
                  <Box
                    sx={{
                      flexGrow: 1,
                      p: 3,
                      overflow: 'auto',
                      backgroundColor: 'background.default',
                    }}
                  >
                    <Routes>
                      <Route path="/" element={<Navigate to="/dashboard" replace />} />
                      <Route path="/dashboard" element={<Dashboard />} />
                      <Route path="/constellation" element={<RiskConstellation />} />
                      <Route path="/portfolio" element={<PortfolioAnalysis />} />
                      <Route path="/settings" element={<Settings />} />
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

// Made with Bob

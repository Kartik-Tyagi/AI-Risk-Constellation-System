import React, { createContext, useContext, useState, useEffect } from 'react';
import { monitoringApi } from '../services/api';

const AppContext = createContext();

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within AppProvider');
  }
  return context;
};

export const AppProvider = ({ children }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [notification, setNotification] = useState(null);
  const [systemHealth, setSystemHealth] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Check system health periodically
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await monitoringApi.getHealth();
        setSystemHealth(response.data);
      } catch (err) {
        console.error('Health check failed:', err);
        setSystemHealth({ status: 'unhealthy' });
      }
    };

    // Initial check
    checkHealth();

    // Check every 30 seconds
    const interval = setInterval(checkHealth, 30000);

    return () => clearInterval(interval);
  }, []);

  // Show notification
  const showNotification = (message, severity = 'info', duration = 5000) => {
    setNotification({ message, severity, duration });
  };

  // Clear notification
  const clearNotification = () => {
    setNotification(null);
  };

  // Show error
  const showError = (message) => {
    setError(message);
    showNotification(message, 'error');
  };

  // Clear error
  const clearError = () => {
    setError(null);
  };

  // Toggle sidebar
  const toggleSidebar = () => {
    setSidebarOpen((prev) => !prev);
  };

  const value = {
    // State
    loading,
    error,
    notification,
    systemHealth,
    sidebarOpen,

    // Actions
    setLoading,
    showError,
    clearError,
    showNotification,
    clearNotification,
    toggleSidebar,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

// Made with Bob
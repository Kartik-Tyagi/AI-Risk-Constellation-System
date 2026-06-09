import React, { createContext, useContext, useState, useEffect } from 'react';

const UserContext = createContext();

export const useUser = () => {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error('useUser must be used within UserProvider');
  }
  return context;
};

// Default user preferences
const defaultPreferences = {
  theme: 'dark',
  visualization: {
    defaultView: '2d', // '2d' or '3d'
    showLabels: true,
    showRiskLevels: true,
    animateTransitions: true,
    nodeSize: 'medium', // 'small', 'medium', 'large'
    edgeThickness: 'medium',
    colorScheme: 'risk', // 'risk', 'type', 'sector'
  },
  dashboard: {
    refreshInterval: 30, // seconds
    showRealTimeUpdates: true,
    defaultTimeRange: '1d', // '1h', '1d', '1w', '1m'
    chartType: 'line', // 'line', 'candlestick', 'area'
  },
  notifications: {
    enabled: true,
    riskAlerts: true,
    marketUpdates: true,
    portfolioChanges: true,
    sound: false,
  },
  advanced: {
    showDebugInfo: false,
    enableExperimentalFeatures: false,
    maxGraphNodes: 1000,
    cacheEnabled: true,
  },
};

export const UserProvider = ({ children }) => {
  const [preferences, setPreferences] = useState(() => {
    // Load preferences from localStorage
    const saved = localStorage.getItem('userPreferences');
    return saved ? { ...defaultPreferences, ...JSON.parse(saved) } : defaultPreferences;
  });

  const [recentPortfolios, setRecentPortfolios] = useState(() => {
    const saved = localStorage.getItem('recentPortfolios');
    return saved ? JSON.parse(saved) : [];
  });

  const [favorites, setFavorites] = useState(() => {
    const saved = localStorage.getItem('favorites');
    return saved ? JSON.parse(saved) : [];
  });

  // Save preferences to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('userPreferences', JSON.stringify(preferences));
  }, [preferences]);

  // Save recent portfolios to localStorage
  useEffect(() => {
    localStorage.setItem('recentPortfolios', JSON.stringify(recentPortfolios));
  }, [recentPortfolios]);

  // Save favorites to localStorage
  useEffect(() => {
    localStorage.setItem('favorites', JSON.stringify(favorites));
  }, [favorites]);

  // Update a specific preference
  const updatePreference = (category, key, value) => {
    setPreferences((prev) => ({
      ...prev,
      [category]: {
        ...prev[category],
        [key]: value,
      },
    }));
  };

  // Update multiple preferences at once
  const updatePreferences = (newPreferences) => {
    setPreferences((prev) => ({
      ...prev,
      ...newPreferences,
    }));
  };

  // Reset preferences to default
  const resetPreferences = () => {
    setPreferences(defaultPreferences);
  };

  // Add portfolio to recent list
  const addRecentPortfolio = (portfolio) => {
    setRecentPortfolios((prev) => {
      // Remove if already exists
      const filtered = prev.filter((p) => p.id !== portfolio.id);
      // Add to beginning and limit to 10
      return [portfolio, ...filtered].slice(0, 10);
    });
  };

  // Clear recent portfolios
  const clearRecentPortfolios = () => {
    setRecentPortfolios([]);
  };

  // Add to favorites
  const addFavorite = (item) => {
    setFavorites((prev) => {
      if (prev.find((f) => f.id === item.id && f.type === item.type)) {
        return prev; // Already in favorites
      }
      return [...prev, { ...item, addedAt: Date.now() }];
    });
  };

  // Remove from favorites
  const removeFavorite = (itemId, itemType) => {
    setFavorites((prev) => prev.filter((f) => !(f.id === itemId && f.type === itemType)));
  };

  // Check if item is favorited
  const isFavorite = (itemId, itemType) => {
    return favorites.some((f) => f.id === itemId && f.type === itemType);
  };

  // Toggle favorite
  const toggleFavorite = (item) => {
    if (isFavorite(item.id, item.type)) {
      removeFavorite(item.id, item.type);
    } else {
      addFavorite(item);
    }
  };

  // Get favorites by type
  const getFavoritesByType = (type) => {
    return favorites.filter((f) => f.type === type);
  };

  const value = {
    // State
    preferences,
    recentPortfolios,
    favorites,

    // Preference actions
    updatePreference,
    updatePreferences,
    resetPreferences,

    // Recent portfolios actions
    addRecentPortfolio,
    clearRecentPortfolios,

    // Favorites actions
    addFavorite,
    removeFavorite,
    isFavorite,
    toggleFavorite,
    getFavoritesByType,
  };

  return <UserContext.Provider value={value}>{children}</UserContext.Provider>;
};

// Made with Bob
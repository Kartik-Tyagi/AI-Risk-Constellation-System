import { useEffect, useCallback, useState } from 'react';
import websocketService from '../services/websocket';

/**
 * Custom hook for WebSocket connections
 * @param {Object} options - Configuration options
 * @returns {Object} - WebSocket state and methods
 */
export const useWebSocket = (options = {}) => {
  const [isConnected, setIsConnected] = useState(websocketService.isConnected());
  const [lastMessage, setLastMessage] = useState(null);
  const [connectionState, setConnectionState] = useState(websocketService.getState());

  useEffect(() => {
    // Update connection state
    const updateState = () => {
      setIsConnected(websocketService.isConnected());
      setConnectionState(websocketService.getState());
    };

    // Listen for connection events
    const unsubscribeConnected = websocketService.on('connected', () => {
      updateState();
      if (options.onConnect) {
        options.onConnect();
      }
    });

    const unsubscribeDisconnected = websocketService.on('disconnected', () => {
      updateState();
      if (options.onDisconnect) {
        options.onDisconnect();
      }
    });

    const unsubscribeReconnecting = websocketService.on('reconnecting', (data) => {
      updateState();
      if (options.onReconnecting) {
        options.onReconnecting(data);
      }
    });

    const unsubscribeError = websocketService.on('error', (data) => {
      if (options.onError) {
        options.onError(data.error);
      }
    });

    // Listen for messages
    const unsubscribeMessage = websocketService.on('message', (data) => {
      setLastMessage(data);
      if (options.onMessage) {
        options.onMessage(data);
      }
    });

    // Initial state update
    updateState();

    // Cleanup
    return () => {
      unsubscribeConnected();
      unsubscribeDisconnected();
      unsubscribeReconnecting();
      unsubscribeError();
      unsubscribeMessage();
    };
  }, [options]);

  const send = useCallback((data) => {
    return websocketService.send(data);
  }, []);

  const subscribe = useCallback((portfolioId) => {
    return websocketService.subscribeToPortfolio(portfolioId);
  }, []);

  const unsubscribe = useCallback((portfolioId) => {
    return websocketService.unsubscribeFromPortfolio(portfolioId);
  }, []);

  return {
    isConnected,
    connectionState,
    lastMessage,
    send,
    subscribe,
    unsubscribe,
  };
};

/**
 * Hook for subscribing to specific WebSocket events
 * @param {string} event - Event name to listen for
 * @param {Function} callback - Callback function
 * @param {Array} dependencies - Dependencies array
 */
export const useWebSocketEvent = (event, callback, dependencies = []) => {
  useEffect(() => {
    const unsubscribe = websocketService.on(event, callback);
    return unsubscribe;
  }, [event, callback, ...dependencies]);
};

/**
 * Hook for subscribing to portfolio updates
 * @param {string} portfolioId - Portfolio ID to subscribe to
 * @param {Function} onUpdate - Callback for updates
 */
export const usePortfolioUpdates = (portfolioId, onUpdate) => {
  const [updates, setUpdates] = useState([]);

  useEffect(() => {
    if (!portfolioId) return;

    // Subscribe to portfolio
    websocketService.subscribeToPortfolio(portfolioId);

    // Listen for risk updates
    const unsubscribeRisk = websocketService.on('risk_update', (data) => {
      if (data.portfolio_id === portfolioId) {
        const update = { ...data, timestamp: Date.now() };
        setUpdates((prev) => [update, ...prev.slice(0, 49)]); // Keep last 50
        if (onUpdate) {
          onUpdate(update);
        }
      }
    });

    // Listen for graph updates
    const unsubscribeGraph = websocketService.on('graph_update', (data) => {
      if (data.portfolio_id === portfolioId) {
        const update = { ...data, timestamp: Date.now() };
        setUpdates((prev) => [update, ...prev.slice(0, 49)]);
        if (onUpdate) {
          onUpdate(update);
        }
      }
    });

    // Listen for market updates
    const unsubscribeMarket = websocketService.on('market_update', (data) => {
      const update = { ...data, timestamp: Date.now() };
      setUpdates((prev) => [update, ...prev.slice(0, 49)]);
      if (onUpdate) {
        onUpdate(update);
      }
    });

    // Cleanup
    return () => {
      websocketService.unsubscribeFromPortfolio(portfolioId);
      unsubscribeRisk();
      unsubscribeGraph();
      unsubscribeMarket();
    };
  }, [portfolioId, onUpdate]);

  const clearUpdates = useCallback(() => {
    setUpdates([]);
  }, []);

  return {
    updates,
    clearUpdates,
  };
};

// Made with Bob
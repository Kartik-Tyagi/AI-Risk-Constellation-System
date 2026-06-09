import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { riskApi, graphApi } from '../services/api';
import websocketService from '../services/websocket';

const RiskContext = createContext();

export const useRisk = () => {
  const context = useContext(RiskContext);
  if (!context) {
    throw new Error('useRisk must be used within RiskProvider');
  }
  return context;
};

export const RiskProvider = ({ children }) => {
  const [selectedPortfolio, setSelectedPortfolio] = useState(null);
  const [riskData, setRiskData] = useState(null);
  const [graphData, setGraphData] = useState(null);
  const [riskDNA, setRiskDNA] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [realTimeUpdates, setRealTimeUpdates] = useState([]);

  // Load risk data for selected portfolio
  const loadRiskData = useCallback(async (portfolioId) => {
    if (!portfolioId) return;

    setLoading(true);
    setError(null);

    try {
      // Load risk analysis
      const riskResponse = await riskApi.analyzePortfolio(portfolioId);
      setRiskData(riskResponse.data);

      // Load graph data
      const graphResponse = await graphApi.getGraph(portfolioId);
      setGraphData(graphResponse.data);

      // Load risk DNA
      const dnaResponse = await riskApi.getRiskDNA(portfolioId);
      setRiskDNA(dnaResponse.data);
    } catch (err) {
      console.error('Error loading risk data:', err);
      setError(err.message || 'Failed to load risk data');
    } finally {
      setLoading(false);
    }
  }, []);

  // Subscribe to real-time updates when portfolio changes
  useEffect(() => {
    if (!selectedPortfolio) return;

    // Subscribe to portfolio updates
    websocketService.subscribeToPortfolio(selectedPortfolio.id);

    // Listen for risk updates
    const unsubscribeRisk = websocketService.on('risk_update', (data) => {
      console.log('Risk update received:', data);
      
      // Add to real-time updates
      setRealTimeUpdates((prev) => [
        { ...data, timestamp: Date.now() },
        ...prev.slice(0, 99), // Keep last 100 updates
      ]);

      // Update risk data if it matches current portfolio
      if (data.portfolio_id === selectedPortfolio.id) {
        setRiskData((prev) => ({
          ...prev,
          ...data.risk_metrics,
        }));
      }
    });

    // Listen for graph updates
    const unsubscribeGraph = websocketService.on('graph_update', (data) => {
      console.log('Graph update received:', data);
      
      if (data.portfolio_id === selectedPortfolio.id) {
        setGraphData((prev) => ({
          ...prev,
          nodes: data.nodes || prev?.nodes,
          edges: data.edges || prev?.edges,
        }));
      }
    });

    // Listen for market updates
    const unsubscribeMarket = websocketService.on('market_update', (data) => {
      console.log('Market update received:', data);
      
      // Update relevant nodes in graph
      if (graphData?.nodes) {
        setGraphData((prev) => ({
          ...prev,
          nodes: prev.nodes.map((node) =>
            node.symbol === data.symbol
              ? { ...node, price: data.price, change: data.change }
              : node
          ),
        }));
      }
    });

    // Load initial data
    loadRiskData(selectedPortfolio.id);

    // Cleanup
    return () => {
      websocketService.unsubscribeFromPortfolio(selectedPortfolio.id);
      unsubscribeRisk();
      unsubscribeGraph();
      unsubscribeMarket();
    };
  }, [selectedPortfolio, loadRiskData, graphData?.nodes]);

  // Refresh risk data
  const refreshRiskData = useCallback(() => {
    if (selectedPortfolio) {
      loadRiskData(selectedPortfolio.id);
    }
  }, [selectedPortfolio, loadRiskData]);

  // Get risk constellation
  const getRiskConstellation = useCallback(async (portfolioId, filters = {}) => {
    try {
      const response = await riskApi.getConstellation(portfolioId, filters);
      return response.data;
    } catch (err) {
      console.error('Error getting risk constellation:', err);
      throw err;
    }
  }, []);

  // Get risk propagation paths
  const getRiskPropagation = useCallback(async (portfolioId, entityId) => {
    try {
      const response = await riskApi.getPropagationPaths(portfolioId, entityId);
      return response.data;
    } catch (err) {
      console.error('Error getting risk propagation:', err);
      throw err;
    }
  }, []);

  // Run stress test
  const runStressTest = useCallback(async (portfolioId, scenario) => {
    try {
      setLoading(true);
      const response = await riskApi.runStressTest(portfolioId, scenario);
      return response.data;
    } catch (err) {
      console.error('Error running stress test:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Get entity details
  const getEntityDetails = useCallback(async (entityId) => {
    try {
      const response = await graphApi.getEntity(entityId);
      return response.data;
    } catch (err) {
      console.error('Error getting entity details:', err);
      throw err;
    }
  }, []);

  // Find path between entities
  const findPath = useCallback(async (sourceId, targetId) => {
    try {
      const response = await graphApi.findPath(sourceId, targetId);
      return response.data;
    } catch (err) {
      console.error('Error finding path:', err);
      throw err;
    }
  }, []);

  // Clear real-time updates
  const clearUpdates = useCallback(() => {
    setRealTimeUpdates([]);
  }, []);

  const value = {
    // State
    selectedPortfolio,
    riskData,
    graphData,
    riskDNA,
    loading,
    error,
    realTimeUpdates,

    // Actions
    setSelectedPortfolio,
    loadRiskData,
    refreshRiskData,
    getRiskConstellation,
    getRiskPropagation,
    runStressTest,
    getEntityDetails,
    findPath,
    clearUpdates,
  };

  return <RiskContext.Provider value={value}>{children}</RiskContext.Provider>;
};

// Made with Bob
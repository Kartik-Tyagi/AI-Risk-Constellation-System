import { useState, useEffect, useCallback } from 'react';
import { useRisk } from '../context/RiskContext';
import { riskApi, graphApi } from '../services/api';

/**
 * Hook for managing risk data with caching and real-time updates
 * @param {string} portfolioId - Portfolio ID
 * @param {Object} options - Configuration options
 * @returns {Object} - Risk data and methods
 */
export const useRiskData = (portfolioId, options = {}) => {
  const { riskData, graphData, loading: contextLoading } = useRisk();
  const [localData, setLocalData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Use context data if available, otherwise use local data
  const data = options.useContext !== false ? riskData : localData;
  const isLoading = options.useContext !== false ? contextLoading : loading;

  // Load risk data
  const loadData = useCallback(async () => {
    if (!portfolioId) return;

    setLoading(true);
    setError(null);

    try {
      const response = await riskApi.analyzePortfolio(portfolioId, options.analysisOptions);
      setLocalData(response.data);
      return response.data;
    } catch (err) {
      setError(err.message || 'Failed to load risk data');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [portfolioId, options.analysisOptions]);

  // Auto-load on mount if enabled
  useEffect(() => {
    if (options.autoLoad !== false && portfolioId) {
      loadData();
    }
  }, [portfolioId, options.autoLoad, loadData]);

  return {
    data,
    loading: isLoading,
    error,
    reload: loadData,
  };
};

/**
 * Hook for risk constellation data
 * @param {string} portfolioId - Portfolio ID
 * @param {Object} filters - Filter options
 * @returns {Object} - Constellation data and methods
 */
export const useRiskConstellation = (portfolioId, filters = {}) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadConstellation = useCallback(async () => {
    if (!portfolioId) return;

    setLoading(true);
    setError(null);

    try {
      const response = await riskApi.getConstellation(portfolioId, filters);
      setData(response.data);
      return response.data;
    } catch (err) {
      setError(err.message || 'Failed to load constellation');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [portfolioId, filters]);

  useEffect(() => {
    loadConstellation();
  }, [loadConstellation]);

  return {
    data,
    loading,
    error,
    reload: loadConstellation,
  };
};

/**
 * Hook for risk propagation analysis
 * @param {string} portfolioId - Portfolio ID
 * @param {string} entityId - Entity ID to analyze
 * @returns {Object} - Propagation data and methods
 */
export const useRiskPropagation = (portfolioId, entityId) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadPropagation = useCallback(async () => {
    if (!portfolioId || !entityId) return;

    setLoading(true);
    setError(null);

    try {
      const response = await riskApi.getPropagationPaths(portfolioId, entityId);
      setData(response.data);
      return response.data;
    } catch (err) {
      setError(err.message || 'Failed to load propagation');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [portfolioId, entityId]);

  useEffect(() => {
    if (entityId) {
      loadPropagation();
    }
  }, [entityId, loadPropagation]);

  return {
    data,
    loading,
    error,
    reload: loadPropagation,
  };
};

/**
 * Hook for risk DNA visualization data
 * @param {string} portfolioId - Portfolio ID
 * @returns {Object} - DNA data and methods
 */
export const useRiskDNA = (portfolioId) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadDNA = useCallback(async () => {
    if (!portfolioId) return;

    setLoading(true);
    setError(null);

    try {
      const response = await riskApi.getRiskDNA(portfolioId);
      setData(response.data);
      return response.data;
    } catch (err) {
      setError(err.message || 'Failed to load risk DNA');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [portfolioId]);

  useEffect(() => {
    loadDNA();
  }, [loadDNA]);

  return {
    data,
    loading,
    error,
    reload: loadDNA,
  };
};

/**
 * Hook for graph data with filtering
 * @param {string} portfolioId - Portfolio ID
 * @param {Object} filters - Filter options
 * @returns {Object} - Graph data and methods
 */
export const useGraphData = (portfolioId, filters = {}) => {
  const { graphData } = useRisk();
  const [filteredData, setFilteredData] = useState(null);

  useEffect(() => {
    if (!graphData) {
      setFilteredData(null);
      return;
    }

    // Apply filters
    let nodes = graphData.nodes || [];
    let edges = graphData.edges || [];

    // Filter by risk level
    if (filters.minRiskLevel !== undefined) {
      nodes = nodes.filter((node) => node.risk_level >= filters.minRiskLevel);
      const nodeIds = new Set(nodes.map((n) => n.id));
      edges = edges.filter((e) => nodeIds.has(e.source) && nodeIds.has(e.target));
    }

    // Filter by entity type
    if (filters.entityTypes && filters.entityTypes.length > 0) {
      nodes = nodes.filter((node) => filters.entityTypes.includes(node.type));
      const nodeIds = new Set(nodes.map((n) => n.id));
      edges = edges.filter((e) => nodeIds.has(e.source) && nodeIds.has(e.target));
    }

    // Filter by search term
    if (filters.searchTerm) {
      const term = filters.searchTerm.toLowerCase();
      nodes = nodes.filter(
        (node) =>
          node.name?.toLowerCase().includes(term) ||
          node.symbol?.toLowerCase().includes(term)
      );
      const nodeIds = new Set(nodes.map((n) => n.id));
      edges = edges.filter((e) => nodeIds.has(e.source) && nodeIds.has(e.target));
    }

    setFilteredData({ nodes, edges });
  }, [graphData, filters]);

  return filteredData || graphData;
};

/**
 * Hook for stress testing
 * @param {string} portfolioId - Portfolio ID
 * @returns {Object} - Stress test methods and results
 */
export const useStressTest = (portfolioId) => {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const runTest = useCallback(
    async (scenario) => {
      if (!portfolioId) return;

      setLoading(true);
      setError(null);

      try {
        const response = await riskApi.runStressTest(portfolioId, scenario);
        setResults(response.data);
        return response.data;
      } catch (err) {
        setError(err.message || 'Failed to run stress test');
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [portfolioId]
  );

  const clearResults = useCallback(() => {
    setResults(null);
    setError(null);
  }, []);

  return {
    results,
    loading,
    error,
    runTest,
    clearResults,
  };
};

// Made with Bob
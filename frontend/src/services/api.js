import axios from 'axios';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_VERSION = '/api/v1';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: `${API_BASE_URL}${API_VERSION}`,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add timestamp to prevent caching
    config.params = {
      ...config.params,
      _t: Date.now(),
    };
    
    // Log request in development
    if (import.meta.env.DEV) {
      console.log(`[API Request] ${config.method.toUpperCase()} ${config.url}`, config.data);
    }
    
    return config;
  },
  (error) => {
    console.error('[API Request Error]', error);
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    // Log response in development
    if (import.meta.env.DEV) {
      console.log(`[API Response] ${response.config.url}`, response.data);
    }
    
    return response;
  },
  (error) => {
    // Handle errors
    const errorMessage = error.response?.data?.detail || error.message || 'An error occurred';
    
    console.error('[API Response Error]', {
      url: error.config?.url,
      status: error.response?.status,
      message: errorMessage,
    });
    
    // Create user-friendly error object
    const apiError = {
      message: errorMessage,
      status: error.response?.status,
      data: error.response?.data,
    };
    
    return Promise.reject(apiError);
  }
);

// ============================================================================
// Portfolio API
// ============================================================================

export const portfolioApi = {
  // Get all portfolios
  getAll: () => apiClient.get('/portfolios'),
  
  // Get portfolio by ID
  getById: (portfolioId) => apiClient.get(`/portfolios/${portfolioId}`),
  
  // Create new portfolio
  create: (portfolioData) => apiClient.post('/portfolios', portfolioData),
  
  // Update portfolio
  update: (portfolioId, portfolioData) => apiClient.put(`/portfolios/${portfolioId}`, portfolioData),
  
  // Delete portfolio
  delete: (portfolioId) => apiClient.delete(`/portfolios/${portfolioId}`),
  
  // Get portfolio positions
  getPositions: (portfolioId) => apiClient.get(`/portfolios/${portfolioId}/positions`),
  
  // Add position to portfolio
  addPosition: (portfolioId, positionData) => apiClient.post(`/portfolios/${portfolioId}/positions`, positionData),
  
  // Get portfolio risk metrics
  getRiskMetrics: (portfolioId) => apiClient.get(`/portfolios/${portfolioId}/risk`),
};

// ============================================================================
// Risk Analysis API
// ============================================================================

export const riskApi = {
  // Analyze portfolio risk
  analyzePortfolio: (portfolioId, options = {}) => 
    apiClient.post(`/risk/analyze/${portfolioId}`, options),
  
  // Get risk constellation graph
  getConstellation: (portfolioId, params = {}) => 
    apiClient.get(`/risk/constellation/${portfolioId}`, { params }),
  
  // Get risk propagation paths
  getPropagationPaths: (portfolioId, entityId) => 
    apiClient.get(`/risk/propagation/${portfolioId}/${entityId}`),
  
  // Get risk DNA
  getRiskDNA: (portfolioId) => 
    apiClient.get(`/risk/dna/${portfolioId}`),
  
  // Get risk scenarios
  getScenarios: (portfolioId) => 
    apiClient.get(`/risk/scenarios/${portfolioId}`),
  
  // Run stress test
  runStressTest: (portfolioId, scenario) => 
    apiClient.post(`/risk/stress-test/${portfolioId}`, scenario),
};

// ============================================================================
// Graph Analysis API
// ============================================================================

export const graphApi = {
  // Get full risk graph
  getGraph: (portfolioId, params = {}) => 
    apiClient.get(`/graph/${portfolioId}`, { params }),
  
  // Get entity details
  getEntity: (entityId) => 
    apiClient.get(`/graph/entity/${entityId}`),
  
  // Get entity relationships
  getRelationships: (entityId, depth = 1) => 
    apiClient.get(`/graph/relationships/${entityId}`, { params: { depth } }),
  
  // Find shortest path between entities
  findPath: (sourceId, targetId) => 
    apiClient.get(`/graph/path/${sourceId}/${targetId}`),
  
  // Get central entities (most connected)
  getCentralEntities: (portfolioId, limit = 10) => 
    apiClient.get(`/graph/central/${portfolioId}`, { params: { limit } }),
  
  // Detect communities/clusters
  detectCommunities: (portfolioId) => 
    apiClient.get(`/graph/communities/${portfolioId}`),
};

// ============================================================================
// Market Data API
// ============================================================================

export const marketApi = {
  // Get market data for entity
  getMarketData: (symbol, params = {}) => 
    apiClient.get(`/market/${symbol}`, { params }),
  
  // Get historical prices
  getHistoricalPrices: (symbol, startDate, endDate) => 
    apiClient.get(`/market/${symbol}/history`, { 
      params: { start_date: startDate, end_date: endDate } 
    }),
  
  // Get real-time quote
  getQuote: (symbol) => 
    apiClient.get(`/market/${symbol}/quote`),
  
  // Get market correlations
  getCorrelations: (symbols) => 
    apiClient.post('/market/correlations', { symbols }),
  
  // Get market volatility
  getVolatility: (symbol, period = 30) => 
    apiClient.get(`/market/${symbol}/volatility`, { params: { period } }),
};

// ============================================================================
// Query API (Natural Language)
// ============================================================================

export const queryApi = {
  // Execute natural language query
  execute: (query, portfolioId = null) => 
    apiClient.post('/query', { query, portfolio_id: portfolioId }),
  
  // Get query suggestions
  getSuggestions: (partial) => 
    apiClient.get('/query/suggestions', { params: { q: partial } }),
  
  // Get query history
  getHistory: (limit = 10) => 
    apiClient.get('/query/history', { params: { limit } }),
};

// ============================================================================
// Monitoring API
// ============================================================================

export const monitoringApi = {
  // Get system health
  getHealth: () => apiClient.get('/monitoring/health'),
  
  // Get detailed health check
  getDetailedHealth: () => apiClient.get('/monitoring/health/detailed'),
  
  // Get API metrics
  getMetrics: () => apiClient.get('/monitoring/metrics'),
  
  // Get request metrics
  getRequestMetrics: (timeRange = '1h') => 
    apiClient.get('/monitoring/metrics/requests', { params: { time_range: timeRange } }),
  
  // Get database metrics
  getDatabaseMetrics: () => apiClient.get('/monitoring/metrics/database'),
  
  // Get ML inference metrics
  getMLMetrics: () => apiClient.get('/monitoring/metrics/ml'),
};

// ============================================================================
// Utility Functions
// ============================================================================

// Generic GET request
export const get = (url, params = {}) => apiClient.get(url, { params });

// Generic POST request
export const post = (url, data = {}) => apiClient.post(url, data);

// Generic PUT request
export const put = (url, data = {}) => apiClient.put(url, data);

// Generic DELETE request
export const del = (url) => apiClient.delete(url);

// Export axios instance for custom requests
export { apiClient };

// Export base URL for WebSocket connections
export const getWebSocketUrl = () => {
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsHost = API_BASE_URL.replace(/^https?:/, '');
  return `${wsProtocol}${wsHost}/ws`;
};

// Made with Bob
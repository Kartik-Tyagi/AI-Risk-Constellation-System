import api from './api';

/**
 * Natural Language Query Service
 * Handles communication with backend NL query processor
 */

class NLQueryService {
  /**
   * Submit a natural language query
   * @param {string} query - The natural language query
   * @returns {Promise} Query results
   */
  async submitQuery(query) {
    try {
      const response = await api.post('/nl-query', { query });
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      console.error('Error submitting NL query:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to process query',
      };
    }
  }

  /**
   * Get query suggestions based on partial input
   * @param {string} partial - Partial query text
   * @returns {Promise} Suggested queries
   */
  async getSuggestions(partial) {
    try {
      const response = await api.get('/nl-query/suggestions', {
        params: { q: partial },
      });
      return response.data.suggestions || [];
    } catch (error) {
      console.error('Error getting suggestions:', error);
      return [];
    }
  }

  /**
   * Parse query response and format for display
   * @param {Object} response - Raw response from backend
   * @returns {Object} Formatted response
   */
  parseResponse(response) {
    if (!response || !response.data) {
      return {
        type: 'error',
        message: 'Invalid response',
      };
    }

    const { query_type, results, visualization_type, metadata } = response.data;

    return {
      type: query_type || 'general',
      results: this.formatResults(results, query_type),
      visualizationType: visualization_type || 'table',
      metadata: metadata || {},
      timestamp: new Date().toISOString(),
    };
  }

  /**
   * Format results based on query type
   * @param {*} results - Raw results
   * @param {string} queryType - Type of query
   * @returns {*} Formatted results
   */
  formatResults(results, queryType) {
    if (!results) return null;

    switch (queryType) {
      case 'risk_assessment':
        return this.formatRiskAssessment(results);
      case 'correlation':
        return this.formatCorrelation(results);
      case 'propagation':
        return this.formatPropagation(results);
      case 'comparison':
        return this.formatComparison(results);
      case 'temporal':
        return this.formatTemporal(results);
      case 'optimization':
        return this.formatOptimization(results);
      default:
        return results;
    }
  }

  /**
   * Format risk assessment results
   */
  formatRiskAssessment(results) {
    if (Array.isArray(results)) {
      return results.map((item) => ({
        entity: item.entity_id || item.name,
        riskLevel: item.risk_level || item.risk_score,
        riskScore: parseFloat(item.risk_score || 0).toFixed(2),
        factors: item.risk_factors || [],
        confidence: item.confidence || 0,
      }));
    }
    return {
      entity: results.entity_id || results.name,
      riskLevel: results.risk_level,
      riskScore: parseFloat(results.risk_score || 0).toFixed(2),
      factors: results.risk_factors || [],
      confidence: results.confidence || 0,
    };
  }

  /**
   * Format correlation results
   */
  formatCorrelation(results) {
    if (Array.isArray(results)) {
      return results.map((item) => ({
        entity1: item.entity1 || item.source,
        entity2: item.entity2 || item.target,
        correlation: parseFloat(item.correlation || 0).toFixed(3),
        strength: this.getCorrelationStrength(item.correlation),
        type: item.correlation >= 0 ? 'positive' : 'negative',
      }));
    }
    return results;
  }

  /**
   * Format propagation results
   */
  formatPropagation(results) {
    return {
      source: results.source_entity,
      affectedEntities: results.affected_entities || [],
      propagationPaths: results.paths || [],
      totalImpact: results.total_impact || 0,
      cascadeDepth: results.cascade_depth || 0,
      timeline: results.timeline || [],
    };
  }

  /**
   * Format comparison results
   */
  formatComparison(results) {
    return {
      entities: results.entities || [],
      metrics: results.metrics || {},
      differences: results.differences || [],
      winner: results.winner || null,
      summary: results.summary || '',
    };
  }

  /**
   * Format temporal results
   */
  formatTemporal(results) {
    return {
      entity: results.entity,
      timeSeries: results.time_series || [],
      trend: results.trend || 'stable',
      predictions: results.predictions || [],
      anomalies: results.anomalies || [],
      statistics: results.statistics || {},
    };
  }

  /**
   * Format optimization results
   */
  formatOptimization(results) {
    return {
      currentAllocation: results.current_allocation || {},
      optimizedAllocation: results.optimized_allocation || {},
      expectedImprovement: results.expected_improvement || 0,
      riskReduction: results.risk_reduction || 0,
      recommendations: results.recommendations || [],
    };
  }

  /**
   * Get correlation strength label
   */
  getCorrelationStrength(correlation) {
    const abs = Math.abs(correlation);
    if (abs >= 0.8) return 'Very Strong';
    if (abs >= 0.6) return 'Strong';
    if (abs >= 0.4) return 'Moderate';
    if (abs >= 0.2) return 'Weak';
    return 'Very Weak';
  }

  /**
   * Export results to various formats
   * @param {Object} results - Formatted results
   * @param {string} format - Export format (json, csv, pdf)
   * @returns {Blob} Exported data
   */
  exportResults(results, format = 'json') {
    switch (format) {
      case 'json':
        return this.exportJSON(results);
      case 'csv':
        return this.exportCSV(results);
      default:
        return this.exportJSON(results);
    }
  }

  /**
   * Export as JSON
   */
  exportJSON(results) {
    const json = JSON.stringify(results, null, 2);
    return new Blob([json], { type: 'application/json' });
  }

  /**
   * Export as CSV
   */
  exportCSV(results) {
    if (!results || !results.results) return null;

    const data = Array.isArray(results.results) ? results.results : [results.results];
    if (data.length === 0) return null;

    // Get headers
    const headers = Object.keys(data[0]);
    const csvRows = [headers.join(',')];

    // Add data rows
    data.forEach((row) => {
      const values = headers.map((header) => {
        const value = row[header];
        if (typeof value === 'object') {
          return JSON.stringify(value);
        }
        return value;
      });
      csvRows.push(values.join(','));
    });

    const csv = csvRows.join('\n');
    return new Blob([csv], { type: 'text/csv' });
  }

  /**
   * Download exported results
   * @param {Blob} blob - Data blob
   * @param {string} filename - File name
   */
  downloadResults(blob, filename) {
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }
}

export default new NLQueryService();

// Made with Bob
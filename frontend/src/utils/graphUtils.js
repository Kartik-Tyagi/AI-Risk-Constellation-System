/**
 * Graph Utilities
 * Helper functions for graph data transformation and layout
 */

/**
 * Transform API graph data to D3-compatible format
 * @param {Object} graphData - Raw graph data from API
 * @returns {Object} - D3-compatible graph data
 */
export const transformGraphData = (graphData) => {
  if (!graphData || !graphData.nodes || !graphData.edges) {
    return { nodes: [], links: [] };
  }

  // Transform nodes
  const nodes = graphData.nodes.map((node) => ({
    id: node.id,
    name: node.name || node.symbol || node.id,
    type: node.type || 'unknown',
    riskLevel: node.risk_level || 0,
    riskScore: node.risk_score || 0,
    value: node.value || 0,
    sector: node.sector,
    symbol: node.symbol,
    metadata: node.metadata || {},
    // D3 force simulation properties
    x: node.x,
    y: node.y,
    fx: node.fx, // Fixed x position
    fy: node.fy, // Fixed y position
  }));

  // Transform edges to links
  const links = graphData.edges.map((edge) => ({
    source: edge.source,
    target: edge.target,
    type: edge.type || 'relationship',
    weight: edge.weight || 1,
    riskContribution: edge.risk_contribution || 0,
    metadata: edge.metadata || {},
  }));

  return { nodes, links };
};

/**
 * Calculate node size based on risk score and value
 * @param {Object} node - Node data
 * @param {Object} options - Size calculation options
 * @returns {number} - Node radius
 */
export const calculateNodeSize = (node, options = {}) => {
  const {
    minSize = 5,
    maxSize = 30,
    sizeBy = 'riskScore', // 'riskScore', 'value', 'connections'
  } = options;

  let size = minSize;

  switch (sizeBy) {
    case 'riskScore':
      // Scale based on risk score (0-100)
      size = minSize + (node.riskScore / 100) * (maxSize - minSize);
      break;
    case 'value':
      // Scale based on value (logarithmic)
      if (node.value > 0) {
        const logValue = Math.log10(node.value + 1);
        size = minSize + (logValue / 10) * (maxSize - minSize);
      }
      break;
    case 'connections':
      // Scale based on number of connections
      const connections = node.connections || 0;
      size = minSize + Math.min(connections / 10, 1) * (maxSize - minSize);
      break;
    default:
      size = (minSize + maxSize) / 2;
  }

  return Math.max(minSize, Math.min(maxSize, size));
};

/**
 * Get node color based on risk level
 * @param {number} riskLevel - Risk level (0-100)
 * @param {string} colorScheme - Color scheme to use
 * @returns {string} - Color hex code
 */
export const getNodeColor = (riskLevel, colorScheme = 'risk') => {
  if (colorScheme === 'risk') {
    // Risk-based color gradient
    if (riskLevel >= 80) return '#f44336'; // Critical - Red
    if (riskLevel >= 60) return '#ff9800'; // High - Orange
    if (riskLevel >= 40) return '#ffeb3b'; // Medium - Yellow
    if (riskLevel >= 20) return '#8bc34a'; // Low - Light Green
    return '#4caf50'; // Very Low - Green
  }

  // Default color
  return '#00bcd4'; // Cyan
};

/**
 * Get node color by type
 * @param {string} type - Node type
 * @returns {string} - Color hex code
 */
export const getNodeColorByType = (type) => {
  const typeColors = {
    stock: '#2196f3', // Blue
    bond: '#4caf50', // Green
    commodity: '#ff9800', // Orange
    currency: '#9c27b0', // Purple
    derivative: '#f44336', // Red
    fund: '#00bcd4', // Cyan
    index: '#ffeb3b', // Yellow
    sector: '#795548', // Brown
    company: '#607d8b', // Blue Grey
    unknown: '#9e9e9e', // Grey
  };

  return typeColors[type.toLowerCase()] || typeColors.unknown;
};

/**
 * Get edge color based on risk contribution
 * @param {number} riskContribution - Risk contribution value
 * @returns {string} - Color with opacity
 */
export const getEdgeColor = (riskContribution) => {
  const opacity = Math.min(Math.abs(riskContribution) / 100, 1);
  
  if (riskContribution > 0) {
    // Positive risk contribution - red
    return `rgba(244, 67, 54, ${opacity})`;
  } else if (riskContribution < 0) {
    // Negative risk contribution (hedging) - green
    return `rgba(76, 175, 80, ${opacity})`;
  }
  
  // Neutral - grey
  return `rgba(158, 158, 158, ${opacity * 0.5})`;
};

/**
 * Get edge width based on weight
 * @param {number} weight - Edge weight
 * @param {Object} options - Width calculation options
 * @returns {number} - Edge width
 */
export const getEdgeWidth = (weight, options = {}) => {
  const { minWidth = 1, maxWidth = 5 } = options;
  const normalizedWeight = Math.min(Math.abs(weight), 1);
  return minWidth + normalizedWeight * (maxWidth - minWidth);
};

/**
 * Filter graph data based on criteria
 * @param {Object} graphData - Graph data
 * @param {Object} filters - Filter criteria
 * @returns {Object} - Filtered graph data
 */
export const filterGraphData = (graphData, filters = {}) => {
  const { minRiskLevel, maxRiskLevel, nodeTypes, searchTerm } = filters;

  let nodes = [...graphData.nodes];
  let links = [...graphData.links];

  // Filter by risk level
  if (minRiskLevel !== undefined || maxRiskLevel !== undefined) {
    nodes = nodes.filter((node) => {
      const risk = node.riskLevel;
      const minOk = minRiskLevel === undefined || risk >= minRiskLevel;
      const maxOk = maxRiskLevel === undefined || risk <= maxRiskLevel;
      return minOk && maxOk;
    });
  }

  // Filter by node types
  if (nodeTypes && nodeTypes.length > 0) {
    nodes = nodes.filter((node) => nodeTypes.includes(node.type));
  }

  // Filter by search term
  if (searchTerm && searchTerm.trim()) {
    const term = searchTerm.toLowerCase();
    nodes = nodes.filter(
      (node) =>
        node.name?.toLowerCase().includes(term) ||
        node.symbol?.toLowerCase().includes(term) ||
        node.id?.toLowerCase().includes(term)
    );
  }

  // Filter links to only include nodes that passed filters
  const nodeIds = new Set(nodes.map((n) => n.id));
  links = links.filter((link) => {
    const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
    const targetId = typeof link.target === 'object' ? link.target.id : link.target;
    return nodeIds.has(sourceId) && nodeIds.has(targetId);
  });

  return { nodes, links };
};

/**
 * Find shortest path between two nodes
 * @param {Object} graphData - Graph data
 * @param {string} sourceId - Source node ID
 * @param {string} targetId - Target node ID
 * @returns {Array} - Array of node IDs in path
 */
export const findShortestPath = (graphData, sourceId, targetId) => {
  const { nodes, links } = graphData;
  
  // Build adjacency list
  const adjacency = new Map();
  nodes.forEach((node) => adjacency.set(node.id, []));
  links.forEach((link) => {
    const source = typeof link.source === 'object' ? link.source.id : link.source;
    const target = typeof link.target === 'object' ? link.target.id : link.target;
    adjacency.get(source)?.push(target);
    adjacency.get(target)?.push(source); // Undirected graph
  });

  // BFS to find shortest path
  const queue = [[sourceId]];
  const visited = new Set([sourceId]);

  while (queue.length > 0) {
    const path = queue.shift();
    const node = path[path.length - 1];

    if (node === targetId) {
      return path;
    }

    const neighbors = adjacency.get(node) || [];
    for (const neighbor of neighbors) {
      if (!visited.has(neighbor)) {
        visited.add(neighbor);
        queue.push([...path, neighbor]);
      }
    }
  }

  return []; // No path found
};

/**
 * Calculate graph statistics
 * @param {Object} graphData - Graph data
 * @returns {Object} - Graph statistics
 */
export const calculateGraphStats = (graphData) => {
  const { nodes, links } = graphData;

  // Calculate degree for each node
  const degrees = new Map();
  nodes.forEach((node) => degrees.set(node.id, 0));
  links.forEach((link) => {
    const source = typeof link.source === 'object' ? link.source.id : link.source;
    const target = typeof link.target === 'object' ? link.target.id : link.target;
    degrees.set(source, (degrees.get(source) || 0) + 1);
    degrees.set(target, (degrees.get(target) || 0) + 1);
  });

  // Find central nodes (highest degree)
  const sortedNodes = [...degrees.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([id, degree]) => ({
      id,
      degree,
      node: nodes.find((n) => n.id === id),
    }));

  // Calculate average risk
  const avgRisk =
    nodes.reduce((sum, node) => sum + node.riskLevel, 0) / nodes.length || 0;

  // Calculate density
  const maxLinks = (nodes.length * (nodes.length - 1)) / 2;
  const density = maxLinks > 0 ? links.length / maxLinks : 0;

  return {
    nodeCount: nodes.length,
    linkCount: links.length,
    averageRisk: avgRisk,
    density: density,
    centralNodes: sortedNodes,
    averageDegree: links.length * 2 / nodes.length || 0,
  };
};

/**
 * Detect collision between nodes
 * @param {Object} node1 - First node
 * @param {Object} node2 - Second node
 * @param {number} padding - Collision padding
 * @returns {boolean} - True if collision detected
 */
export const detectCollision = (node1, node2, padding = 0) => {
  const dx = node1.x - node2.x;
  const dy = node1.y - node2.y;
  const distance = Math.sqrt(dx * dx + dy * dy);
  const minDistance = (node1.radius || 10) + (node2.radius || 10) + padding;
  return distance < minDistance;
};

/**
 * Optimize graph layout for performance
 * @param {Object} graphData - Graph data
 * @param {Object} options - Optimization options
 * @returns {Object} - Optimized graph data
 */
export const optimizeGraphLayout = (graphData, options = {}) => {
  const { maxNodes = 1000, clusterThreshold = 50 } = options;
  let { nodes, links } = graphData;

  // If too many nodes, cluster them
  if (nodes.length > maxNodes) {
    // Group nodes by type or sector
    const clusters = new Map();
    nodes.forEach((node) => {
      const key = node.sector || node.type || 'other';
      if (!clusters.has(key)) {
        clusters.set(key, []);
      }
      clusters.get(key).push(node);
    });

    // Create cluster nodes
    const clusterNodes = [];
    const clusterLinks = [];
    
    clusters.forEach((clusterNodes, key) => {
      if (clusterNodes.length > clusterThreshold) {
        // Create a cluster node
        const avgRisk =
          clusterNodes.reduce((sum, n) => sum + n.riskLevel, 0) / clusterNodes.length;
        
        clusterNodes.push({
          id: `cluster_${key}`,
          name: `${key} (${clusterNodes.length} items)`,
          type: 'cluster',
          riskLevel: avgRisk,
          children: clusterNodes,
          isCluster: true,
        });
      } else {
        clusterNodes.push(...clusterNodes);
      }
    });

    nodes = clusterNodes;
    // Rebuild links for clusters
    // (simplified - in production, aggregate links between clusters)
  }

  return { nodes, links };
};

// Made with Bob
/**
 * Graph Rendering Optimizations
 * WebGL acceleration, level of detail, viewport culling, and debounced updates
 */

// ============================================================================
// Level of Detail (LOD) Management
// ============================================================================

/**
 * LOD Manager for graph rendering
 * Adjusts detail level based on zoom and node count
 */
export class LODManager {
  constructor(config = {}) {
    this.config = {
      minZoom: config.minZoom || 0.1,
      maxZoom: config.maxZoom || 10,
      lodLevels: config.lodLevels || [
        { zoom: 0.5, maxNodes: 100, detail: 'low' },
        { zoom: 1.0, maxNodes: 500, detail: 'medium' },
        { zoom: 2.0, maxNodes: 1000, detail: 'high' },
        { zoom: 5.0, maxNodes: Infinity, detail: 'ultra' }
      ]
    };
  }
  
  /**
   * Get appropriate LOD level based on zoom and node count
   * @param {number} zoom - Current zoom level
   * @param {number} nodeCount - Number of nodes
   * @returns {string} LOD level (low, medium, high, ultra)
   */
  getLODLevel(zoom, nodeCount) {
    for (const level of this.config.lodLevels) {
      if (zoom <= level.zoom && nodeCount <= level.maxNodes) {
        return level.detail;
      }
    }
    return 'low';
  }
  
  /**
   * Get rendering settings for LOD level
   * @param {string} lodLevel - LOD level
   * @returns {Object} Rendering settings
   */
  getRenderSettings(lodLevel) {
    const settings = {
      low: {
        renderLabels: false,
        renderEdges: false,
        nodeDetail: 'circle',
        edgeDetail: 'none',
        particleEffects: false,
        shadows: false
      },
      medium: {
        renderLabels: true,
        renderEdges: true,
        nodeDetail: 'circle',
        edgeDetail: 'line',
        particleEffects: false,
        shadows: false
      },
      high: {
        renderLabels: true,
        renderEdges: true,
        nodeDetail: 'detailed',
        edgeDetail: 'curved',
        particleEffects: true,
        shadows: false
      },
      ultra: {
        renderLabels: true,
        renderEdges: true,
        nodeDetail: 'detailed',
        edgeDetail: 'curved',
        particleEffects: true,
        shadows: true
      }
    };
    
    return settings[lodLevel] || settings.low;
  }
  
  /**
   * Should render node based on LOD
   * @param {Object} node - Node object
   * @param {string} lodLevel - LOD level
   * @returns {boolean} Whether to render node
   */
  shouldRenderNode(node, lodLevel) {
    if (lodLevel === 'ultra' || lodLevel === 'high') return true;
    if (lodLevel === 'medium') return node.importance > 0.3;
    return node.importance > 0.7; // Only important nodes in low LOD
  }
  
  /**
   * Should render edge based on LOD
   * @param {Object} edge - Edge object
   * @param {string} lodLevel - LOD level
   * @returns {boolean} Whether to render edge
   */
  shouldRenderEdge(edge, lodLevel) {
    if (lodLevel === 'ultra' || lodLevel === 'high') return true;
    if (lodLevel === 'medium') return edge.weight > 0.3;
    return false; // No edges in low LOD
  }
}

// ============================================================================
// Viewport Culling
// ============================================================================

/**
 * Viewport Culler for efficient rendering
 * Only renders objects within viewport
 */
export class ViewportCuller {
  constructor(padding = 100) {
    this.padding = padding; // Extra padding around viewport
  }
  
  /**
   * Check if point is in viewport
   * @param {number} x - X coordinate
   * @param {number} y - Y coordinate
   * @param {Object} viewport - Viewport bounds
   * @returns {boolean} Whether point is visible
   */
  isPointInViewport(x, y, viewport) {
    return (
      x >= viewport.x - this.padding &&
      x <= viewport.x + viewport.width + this.padding &&
      y >= viewport.y - this.padding &&
      y <= viewport.y + viewport.height + this.padding
    );
  }
  
  /**
   * Check if node is in viewport
   * @param {Object} node - Node with x, y coordinates
   * @param {Object} viewport - Viewport bounds
   * @returns {boolean} Whether node is visible
   */
  isNodeVisible(node, viewport) {
    return this.isPointInViewport(node.x, node.y, viewport);
  }
  
  /**
   * Check if edge is in viewport
   * @param {Object} edge - Edge with source and target nodes
   * @param {Object} viewport - Viewport bounds
   * @returns {boolean} Whether edge is visible
   */
  isEdgeVisible(edge, viewport) {
    // Edge is visible if either endpoint is visible
    return (
      this.isNodeVisible(edge.source, viewport) ||
      this.isNodeVisible(edge.target, viewport)
    );
  }
  
  /**
   * Filter nodes by viewport
   * @param {Array} nodes - All nodes
   * @param {Object} viewport - Viewport bounds
   * @returns {Array} Visible nodes
   */
  filterVisibleNodes(nodes, viewport) {
    return nodes.filter(node => this.isNodeVisible(node, viewport));
  }
  
  /**
   * Filter edges by viewport
   * @param {Array} edges - All edges
   * @param {Object} viewport - Viewport bounds
   * @returns {Array} Visible edges
   */
  filterVisibleEdges(edges, viewport) {
    return edges.filter(edge => this.isEdgeVisible(edge, viewport));
  }
  
  /**
   * Get viewport bounds from camera
   * @param {Object} camera - Camera object with position and zoom
   * @param {number} width - Canvas width
   * @param {number} height - Canvas height
   * @returns {Object} Viewport bounds
   */
  getViewportBounds(camera, width, height) {
    const zoom = camera.zoom || 1;
    const viewWidth = width / zoom;
    const viewHeight = height / zoom;
    
    return {
      x: camera.x - viewWidth / 2,
      y: camera.y - viewHeight / 2,
      width: viewWidth,
      height: viewHeight
    };
  }
}

// ============================================================================
// WebGL Optimization Utilities
// ============================================================================

/**
 * WebGL Buffer Manager
 * Manages vertex buffers for efficient rendering
 */
export class WebGLBufferManager {
  constructor(gl) {
    this.gl = gl;
    this.buffers = new Map();
  }
  
  /**
   * Create or update buffer
   * @param {string} name - Buffer name
   * @param {Float32Array} data - Buffer data
   * @param {number} usage - Buffer usage (STATIC_DRAW, DYNAMIC_DRAW)
   * @returns {WebGLBuffer} Buffer object
   */
  createBuffer(name, data, usage = null) {
    const gl = this.gl;
    usage = usage || gl.STATIC_DRAW;
    
    let buffer = this.buffers.get(name);
    
    if (!buffer) {
      buffer = gl.createBuffer();
      this.buffers.set(name, buffer);
    }
    
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
    gl.bufferData(gl.ARRAY_BUFFER, data, usage);
    
    return buffer;
  }
  
  /**
   * Get buffer by name
   * @param {string} name - Buffer name
   * @returns {WebGLBuffer} Buffer object
   */
  getBuffer(name) {
    return this.buffers.get(name);
  }
  
  /**
   * Delete buffer
   * @param {string} name - Buffer name
   */
  deleteBuffer(name) {
    const buffer = this.buffers.get(name);
    if (buffer) {
      this.gl.deleteBuffer(buffer);
      this.buffers.delete(name);
    }
  }
  
  /**
   * Clear all buffers
   */
  clearAll() {
    for (const buffer of this.buffers.values()) {
      this.gl.deleteBuffer(buffer);
    }
    this.buffers.clear();
  }
}

/**
 * WebGL Batch Renderer
 * Batches draw calls for better performance
 */
export class WebGLBatchRenderer {
  constructor(maxBatchSize = 10000) {
    this.maxBatchSize = maxBatchSize;
    this.batches = [];
    this.currentBatch = null;
  }
  
  /**
   * Start new batch
   * @param {string} type - Batch type (nodes, edges, etc.)
   */
  startBatch(type) {
    this.currentBatch = {
      type,
      vertices: [],
      colors: [],
      indices: [],
      count: 0
    };
  }
  
  /**
   * Add item to current batch
   * @param {Array} vertices - Vertex data
   * @param {Array} colors - Color data
   * @param {Array} indices - Index data
   */
  addToBatch(vertices, colors, indices) {
    if (!this.currentBatch) return;
    
    const batch = this.currentBatch;
    const offset = batch.vertices.length / 2; // Assuming 2D vertices
    
    batch.vertices.push(...vertices);
    batch.colors.push(...colors);
    batch.indices.push(...indices.map(i => i + offset));
    batch.count++;
    
    // Flush if batch is full
    if (batch.count >= this.maxBatchSize) {
      this.flushBatch();
    }
  }
  
  /**
   * Flush current batch
   */
  flushBatch() {
    if (this.currentBatch && this.currentBatch.count > 0) {
      this.batches.push(this.currentBatch);
      this.currentBatch = null;
    }
  }
  
  /**
   * Get all batches
   * @returns {Array} All batches
   */
  getBatches() {
    this.flushBatch();
    return this.batches;
  }
  
  /**
   * Clear all batches
   */
  clear() {
    this.batches = [];
    this.currentBatch = null;
  }
}

// ============================================================================
// Update Debouncing for Graph
// ============================================================================

/**
 * Graph Update Manager
 * Debounces and batches graph updates
 */
export class GraphUpdateManager {
  constructor(updateInterval = 16) { // ~60fps
    this.updateInterval = updateInterval;
    this.pendingUpdates = new Set();
    this.updateTimer = null;
    this.callbacks = [];
  }
  
  /**
   * Schedule update for node
   * @param {string} nodeId - Node ID
   */
  scheduleNodeUpdate(nodeId) {
    this.pendingUpdates.add(`node:${nodeId}`);
    this.scheduleUpdate();
  }
  
  /**
   * Schedule update for edge
   * @param {string} edgeId - Edge ID
   */
  scheduleEdgeUpdate(edgeId) {
    this.pendingUpdates.add(`edge:${edgeId}`);
    this.scheduleUpdate();
  }
  
  /**
   * Schedule full graph update
   */
  scheduleFullUpdate() {
    this.pendingUpdates.add('full');
    this.scheduleUpdate();
  }
  
  /**
   * Schedule update execution
   */
  scheduleUpdate() {
    if (this.updateTimer) return;
    
    this.updateTimer = setTimeout(() => {
      this.executeUpdates();
    }, this.updateInterval);
  }
  
  /**
   * Execute pending updates
   */
  executeUpdates() {
    if (this.pendingUpdates.size === 0) return;
    
    const updates = Array.from(this.pendingUpdates);
    this.pendingUpdates.clear();
    this.updateTimer = null;
    
    // Notify callbacks
    this.callbacks.forEach(callback => callback(updates));
  }
  
  /**
   * Register update callback
   * @param {Function} callback - Callback function
   */
  onUpdate(callback) {
    this.callbacks.push(callback);
  }
  
  /**
   * Clear all pending updates
   */
  clear() {
    this.pendingUpdates.clear();
    if (this.updateTimer) {
      clearTimeout(this.updateTimer);
      this.updateTimer = null;
    }
  }
}

// ============================================================================
// Spatial Indexing for Fast Lookups
// ============================================================================

/**
 * Quadtree for spatial indexing
 * Enables fast node lookups by position
 */
export class Quadtree {
  constructor(bounds, capacity = 4, maxDepth = 8, depth = 0) {
    this.bounds = bounds; // {x, y, width, height}
    this.capacity = capacity;
    this.maxDepth = maxDepth;
    this.depth = depth;
    this.nodes = [];
    this.divided = false;
    this.children = null;
  }
  
  /**
   * Insert node into quadtree
   * @param {Object} node - Node with x, y coordinates
   * @returns {boolean} Success status
   */
  insert(node) {
    if (!this.contains(node)) return false;
    
    if (this.nodes.length < this.capacity || this.depth >= this.maxDepth) {
      this.nodes.push(node);
      return true;
    }
    
    if (!this.divided) {
      this.subdivide();
    }
    
    return (
      this.children.ne.insert(node) ||
      this.children.nw.insert(node) ||
      this.children.se.insert(node) ||
      this.children.sw.insert(node)
    );
  }
  
  /**
   * Check if point is in bounds
   * @param {Object} node - Node with x, y coordinates
   * @returns {boolean} Whether node is in bounds
   */
  contains(node) {
    return (
      node.x >= this.bounds.x &&
      node.x < this.bounds.x + this.bounds.width &&
      node.y >= this.bounds.y &&
      node.y < this.bounds.y + this.bounds.height
    );
  }
  
  /**
   * Subdivide quadtree
   */
  subdivide() {
    const x = this.bounds.x;
    const y = this.bounds.y;
    const w = this.bounds.width / 2;
    const h = this.bounds.height / 2;
    
    this.children = {
      ne: new Quadtree({ x: x + w, y, width: w, height: h }, this.capacity, this.maxDepth, this.depth + 1),
      nw: new Quadtree({ x, y, width: w, height: h }, this.capacity, this.maxDepth, this.depth + 1),
      se: new Quadtree({ x: x + w, y: y + h, width: w, height: h }, this.capacity, this.maxDepth, this.depth + 1),
      sw: new Quadtree({ x, y: y + h, width: w, height: h }, this.capacity, this.maxDepth, this.depth + 1)
    };
    
    this.divided = true;
    
    // Redistribute nodes
    for (const node of this.nodes) {
      this.children.ne.insert(node) ||
      this.children.nw.insert(node) ||
      this.children.se.insert(node) ||
      this.children.sw.insert(node);
    }
    
    this.nodes = [];
  }
  
  /**
   * Query nodes in range
   * @param {Object} range - Range bounds {x, y, width, height}
   * @returns {Array} Nodes in range
   */
  query(range) {
    const found = [];
    
    if (!this.intersects(range)) return found;
    
    for (const node of this.nodes) {
      if (this.pointInRange(node, range)) {
        found.push(node);
      }
    }
    
    if (this.divided) {
      found.push(...this.children.ne.query(range));
      found.push(...this.children.nw.query(range));
      found.push(...this.children.se.query(range));
      found.push(...this.children.sw.query(range));
    }
    
    return found;
  }
  
  /**
   * Check if range intersects bounds
   * @param {Object} range - Range bounds
   * @returns {boolean} Whether ranges intersect
   */
  intersects(range) {
    return !(
      range.x > this.bounds.x + this.bounds.width ||
      range.x + range.width < this.bounds.x ||
      range.y > this.bounds.y + this.bounds.height ||
      range.y + range.height < this.bounds.y
    );
  }
  
  /**
   * Check if point is in range
   * @param {Object} node - Node with x, y coordinates
   * @param {Object} range - Range bounds
   * @returns {boolean} Whether point is in range
   */
  pointInRange(node, range) {
    return (
      node.x >= range.x &&
      node.x < range.x + range.width &&
      node.y >= range.y &&
      node.y < range.y + range.height
    );
  }
}

// ============================================================================
// Export all utilities
// ============================================================================

export default {
  LODManager,
  ViewportCuller,
  WebGLBufferManager,
  WebGLBatchRenderer,
  GraphUpdateManager,
  Quadtree
};

// Made with Bob

import { getWebSocketUrl } from './api';

/**
 * WebSocket Service for Real-Time Updates
 * Manages WebSocket connection with automatic reconnection
 */
class WebSocketService {
  constructor() {
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000; // Start with 1 second
    this.maxReconnectDelay = 30000; // Max 30 seconds
    this.listeners = new Map();
    this.isConnecting = false;
    this.isManualClose = false;
  }

  /**
   * Connect to WebSocket server
   */
  connect() {
    if (this.ws?.readyState === WebSocket.OPEN || this.isConnecting) {
      console.log('[WebSocket] Already connected or connecting');
      return;
    }

    this.isConnecting = true;
    this.isManualClose = false;
    const wsUrl = getWebSocketUrl();

    console.log('[WebSocket] Connecting to:', wsUrl);

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = this.handleOpen.bind(this);
      this.ws.onmessage = this.handleMessage.bind(this);
      this.ws.onerror = this.handleError.bind(this);
      this.ws.onclose = this.handleClose.bind(this);
    } catch (error) {
      console.error('[WebSocket] Connection error:', error);
      this.isConnecting = false;
      this.scheduleReconnect();
    }
  }

  /**
   * Handle WebSocket open event
   */
  handleOpen(event) {
    console.log('[WebSocket] Connected successfully');
    this.isConnecting = false;
    this.reconnectAttempts = 0;
    this.reconnectDelay = 1000;

    // Notify listeners
    this.emit('connected', { timestamp: Date.now() });
  }

  /**
   * Handle incoming WebSocket messages
   */
  handleMessage(event) {
    try {
      const data = JSON.parse(event.data);
      console.log('[WebSocket] Message received:', data);

      // Emit to specific event listeners
      if (data.type) {
        this.emit(data.type, data);
      }

      // Emit to general message listeners
      this.emit('message', data);
    } catch (error) {
      console.error('[WebSocket] Error parsing message:', error);
    }
  }

  /**
   * Handle WebSocket error
   */
  handleError(error) {
    console.error('[WebSocket] Error:', error);
    this.emit('error', { error, timestamp: Date.now() });
  }

  /**
   * Handle WebSocket close event
   */
  handleClose(event) {
    console.log('[WebSocket] Connection closed:', event.code, event.reason);
    this.isConnecting = false;

    // Notify listeners
    this.emit('disconnected', {
      code: event.code,
      reason: event.reason,
      timestamp: Date.now(),
    });

    // Attempt to reconnect if not manually closed
    if (!this.isManualClose && !event.wasClean) {
      this.scheduleReconnect();
    }
  }

  /**
   * Schedule reconnection attempt
   */
  scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('[WebSocket] Max reconnection attempts reached');
      this.emit('reconnect_failed', {
        attempts: this.reconnectAttempts,
        timestamp: Date.now(),
      });
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(
      this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1),
      this.maxReconnectDelay
    );

    console.log(
      `[WebSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`
    );

    this.emit('reconnecting', {
      attempt: this.reconnectAttempts,
      delay,
      timestamp: Date.now(),
    });

    setTimeout(() => {
      this.connect();
    }, delay);
  }

  /**
   * Send message through WebSocket
   */
  send(data) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      const message = typeof data === 'string' ? data : JSON.stringify(data);
      this.ws.send(message);
      console.log('[WebSocket] Message sent:', data);
      return true;
    } else {
      console.warn('[WebSocket] Cannot send message - not connected');
      return false;
    }
  }

  /**
   * Subscribe to portfolio updates
   */
  subscribeToPortfolio(portfolioId) {
    return this.send({
      action: 'subscribe',
      portfolio_id: portfolioId,
    });
  }

  /**
   * Unsubscribe from portfolio updates
   */
  unsubscribeFromPortfolio(portfolioId) {
    return this.send({
      action: 'unsubscribe',
      portfolio_id: portfolioId,
    });
  }

  /**
   * Subscribe to specific risk updates
   */
  subscribeToRiskUpdates(portfolioId, updateTypes = []) {
    return this.send({
      action: 'subscribe_risk',
      portfolio_id: portfolioId,
      update_types: updateTypes,
    });
  }

  /**
   * Add event listener
   */
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);

    // Return unsubscribe function
    return () => this.off(event, callback);
  }

  /**
   * Remove event listener
   */
  off(event, callback) {
    if (!this.listeners.has(event)) return;

    const callbacks = this.listeners.get(event);
    const index = callbacks.indexOf(callback);
    if (index > -1) {
      callbacks.splice(index, 1);
    }

    if (callbacks.length === 0) {
      this.listeners.delete(event);
    }
  }

  /**
   * Emit event to listeners
   */
  emit(event, data) {
    if (!this.listeners.has(event)) return;

    const callbacks = this.listeners.get(event);
    callbacks.forEach((callback) => {
      try {
        callback(data);
      } catch (error) {
        console.error(`[WebSocket] Error in ${event} listener:`, error);
      }
    });
  }

  /**
   * Close WebSocket connection
   */
  disconnect() {
    this.isManualClose = true;
    if (this.ws) {
      this.ws.close(1000, 'Manual disconnect');
      this.ws = null;
    }
    console.log('[WebSocket] Disconnected manually');
  }

  /**
   * Get connection state
   */
  getState() {
    if (!this.ws) return 'CLOSED';
    
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING:
        return 'CONNECTING';
      case WebSocket.OPEN:
        return 'OPEN';
      case WebSocket.CLOSING:
        return 'CLOSING';
      case WebSocket.CLOSED:
        return 'CLOSED';
      default:
        return 'UNKNOWN';
    }
  }

  /**
   * Check if connected
   */
  isConnected() {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

// Create singleton instance
const websocketService = new WebSocketService();

// Auto-connect on module load
if (typeof window !== 'undefined') {
  websocketService.connect();
}

export default websocketService;

// Made with Bob
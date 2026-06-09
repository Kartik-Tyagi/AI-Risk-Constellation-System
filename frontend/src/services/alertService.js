/**
 * Alert Service
 * Manages alerts, notifications, and alert rules
 */

class AlertService {
  constructor() {
    this.storageKey = 'risk-alerts';
    this.rulesKey = 'alert-rules';
    this.listeners = [];
  }

  /**
   * Get all alerts
   * @returns {Array} List of alerts
   */
  async getAlerts() {
    try {
      const stored = localStorage.getItem(this.storageKey);
      return stored ? JSON.parse(stored) : this.getDefaultAlerts();
    } catch (error) {
      console.error('Error getting alerts:', error);
      return [];
    }
  }

  /**
   * Get default/sample alerts
   */
  getDefaultAlerts() {
    return [
      {
        id: '1',
        type: 'threshold_breach',
        severity: 'critical',
        message: 'Risk threshold exceeded for portfolio TECH-001',
        entity_id: 'TECH-001',
        timestamp: new Date().toISOString(),
        acknowledged: false,
        details: {
          threshold: 75,
          current_value: 89,
          breach_percentage: 18.7,
        },
      },
      {
        id: '2',
        type: 'cascade_detected',
        severity: 'warning',
        message: 'Potential risk cascade detected from BANK-005',
        entity_id: 'BANK-005',
        timestamp: new Date(Date.now() - 3600000).toISOString(),
        acknowledged: false,
        details: {
          affected_entities: 12,
          cascade_depth: 3,
          estimated_impact: 0.45,
        },
      },
      {
        id: '3',
        type: 'anomaly_detected',
        severity: 'warning',
        message: 'Unusual risk pattern detected in energy sector',
        entity_id: 'ENERGY-SECTOR',
        timestamp: new Date(Date.now() - 7200000).toISOString(),
        acknowledged: true,
        details: {
          anomaly_score: 0.87,
          deviation: 2.3,
          pattern_type: 'sudden_spike',
        },
      },
    ];
  }

  /**
   * Add new alert
   * @param {Object} alert - Alert object
   */
  async addAlert(alert) {
    try {
      const alerts = await this.getAlerts();
      const newAlert = {
        ...alert,
        id: alert.id || Date.now().toString(),
        timestamp: alert.timestamp || new Date().toISOString(),
        acknowledged: false,
      };
      
      alerts.unshift(newAlert);
      localStorage.setItem(this.storageKey, JSON.stringify(alerts));
      
      // Notify listeners
      this.notifyListeners('alert_added', newAlert);
      
      return newAlert;
    } catch (error) {
      console.error('Error adding alert:', error);
      return null;
    }
  }

  /**
   * Acknowledge alert
   * @param {string} alertId - Alert ID
   */
  async acknowledgeAlert(alertId) {
    try {
      const alerts = await this.getAlerts();
      const updatedAlerts = alerts.map((alert) =>
        alert.id === alertId
          ? { ...alert, acknowledged: true, acknowledged_at: new Date().toISOString() }
          : alert
      );
      
      localStorage.setItem(this.storageKey, JSON.stringify(updatedAlerts));
      this.notifyListeners('alert_acknowledged', alertId);
      
      return true;
    } catch (error) {
      console.error('Error acknowledging alert:', error);
      return false;
    }
  }

  /**
   * Dismiss/delete alert
   * @param {string} alertId - Alert ID
   */
  async dismissAlert(alertId) {
    try {
      const alerts = await this.getAlerts();
      const updatedAlerts = alerts.filter((alert) => alert.id !== alertId);
      
      localStorage.setItem(this.storageKey, JSON.stringify(updatedAlerts));
      this.notifyListeners('alert_dismissed', alertId);
      
      return true;
    } catch (error) {
      console.error('Error dismissing alert:', error);
      return false;
    }
  }

  /**
   * Clear all alerts
   */
  async clearAllAlerts() {
    try {
      localStorage.setItem(this.storageKey, JSON.stringify([]));
      this.notifyListeners('alerts_cleared');
      return true;
    } catch (error) {
      console.error('Error clearing alerts:', error);
      return false;
    }
  }

  /**
   * Show toast notification
   * @param {Object} alert - Alert object
   */
  showToast(alert) {
    const notification = {
      title: this.getAlertTypeTitle(alert.type),
      message: alert.message,
      severity: alert.severity,
      entity_id: alert.entity_id,
      timestamp: alert.timestamp,
      actions: this.getAlertActions(alert),
    };

    // Dispatch custom event
    window.dispatchEvent(
      new CustomEvent('showToast', { detail: notification })
    );
  }

  /**
   * Get alert type title
   */
  getAlertTypeTitle(type) {
    const titles = {
      threshold_breach: 'Risk Threshold Breach',
      cascade_detected: 'Risk Cascade Detected',
      anomaly_detected: 'Anomaly Detected',
      model_prediction: 'Model Prediction Alert',
    };
    return titles[type] || 'Alert';
  }

  /**
   * Get alert actions
   */
  getAlertActions(alert) {
    const actions = [
      {
        label: 'View',
        handler: (notification) => {
          window.location.href = `/alerts/${alert.id}`;
        },
      },
    ];

    if (!alert.acknowledged) {
      actions.push({
        label: 'Acknowledge',
        handler: async (notification) => {
          await this.acknowledgeAlert(alert.id);
        },
      });
    }

    return actions;
  }

  /**
   * Get alert rules
   */
  async getAlertRules() {
    try {
      const stored = localStorage.getItem(this.rulesKey);
      return stored ? JSON.parse(stored) : this.getDefaultRules();
    } catch (error) {
      console.error('Error getting alert rules:', error);
      return [];
    }
  }

  /**
   * Get default alert rules
   */
  getDefaultRules() {
    return [
      {
        id: '1',
        name: 'High Risk Threshold',
        type: 'threshold_breach',
        enabled: true,
        conditions: {
          metric: 'risk_score',
          operator: '>',
          value: 75,
        },
        severity: 'critical',
      },
      {
        id: '2',
        name: 'Risk Cascade Detection',
        type: 'cascade_detected',
        enabled: true,
        conditions: {
          cascade_depth: 3,
          affected_entities: 10,
        },
        severity: 'warning',
      },
      {
        id: '3',
        name: 'Anomaly Detection',
        type: 'anomaly_detected',
        enabled: true,
        conditions: {
          anomaly_score: 0.8,
          deviation: 2.0,
        },
        severity: 'warning',
      },
      {
        id: '4',
        name: 'Model Prediction Alert',
        type: 'model_prediction',
        enabled: true,
        conditions: {
          confidence: 0.9,
          predicted_risk: 'high',
        },
        severity: 'info',
      },
    ];
  }

  /**
   * Save alert rule
   */
  async saveAlertRule(rule) {
    try {
      const rules = await this.getAlertRules();
      const existingIndex = rules.findIndex((r) => r.id === rule.id);
      
      if (existingIndex >= 0) {
        rules[existingIndex] = rule;
      } else {
        rule.id = Date.now().toString();
        rules.push(rule);
      }
      
      localStorage.setItem(this.rulesKey, JSON.stringify(rules));
      return true;
    } catch (error) {
      console.error('Error saving alert rule:', error);
      return false;
    }
  }

  /**
   * Delete alert rule
   */
  async deleteAlertRule(ruleId) {
    try {
      const rules = await this.getAlertRules();
      const updatedRules = rules.filter((rule) => rule.id !== ruleId);
      
      localStorage.setItem(this.rulesKey, JSON.stringify(updatedRules));
      return true;
    } catch (error) {
      console.error('Error deleting alert rule:', error);
      return false;
    }
  }

  /**
   * Evaluate alert rules against data
   */
  async evaluateRules(data) {
    const rules = await this.getAlertRules();
    const triggeredAlerts = [];

    for (const rule of rules) {
      if (!rule.enabled) continue;

      const triggered = this.evaluateRule(rule, data);
      if (triggered) {
        const alert = {
          type: rule.type,
          severity: rule.severity,
          message: this.generateAlertMessage(rule, data),
          entity_id: data.entity_id,
          details: data,
        };
        
        triggeredAlerts.push(alert);
        await this.addAlert(alert);
        this.showToast(alert);
      }
    }

    return triggeredAlerts;
  }

  /**
   * Evaluate single rule
   */
  evaluateRule(rule, data) {
    const { conditions } = rule;

    switch (rule.type) {
      case 'threshold_breach':
        return this.evaluateThreshold(conditions, data);
      case 'cascade_detected':
        return this.evaluateCascade(conditions, data);
      case 'anomaly_detected':
        return this.evaluateAnomaly(conditions, data);
      case 'model_prediction':
        return this.evaluatePrediction(conditions, data);
      default:
        return false;
    }
  }

  /**
   * Evaluate threshold condition
   */
  evaluateThreshold(conditions, data) {
    const value = data[conditions.metric];
    const threshold = conditions.value;

    switch (conditions.operator) {
      case '>':
        return value > threshold;
      case '>=':
        return value >= threshold;
      case '<':
        return value < threshold;
      case '<=':
        return value <= threshold;
      case '==':
        return value === threshold;
      default:
        return false;
    }
  }

  /**
   * Evaluate cascade condition
   */
  evaluateCascade(conditions, data) {
    return (
      data.cascade_depth >= conditions.cascade_depth &&
      data.affected_entities >= conditions.affected_entities
    );
  }

  /**
   * Evaluate anomaly condition
   */
  evaluateAnomaly(conditions, data) {
    return (
      data.anomaly_score >= conditions.anomaly_score &&
      data.deviation >= conditions.deviation
    );
  }

  /**
   * Evaluate prediction condition
   */
  evaluatePrediction(conditions, data) {
    return (
      data.confidence >= conditions.confidence &&
      data.predicted_risk === conditions.predicted_risk
    );
  }

  /**
   * Generate alert message
   */
  generateAlertMessage(rule, data) {
    switch (rule.type) {
      case 'threshold_breach':
        return `${rule.name}: ${data[rule.conditions.metric]} exceeds threshold of ${rule.conditions.value}`;
      case 'cascade_detected':
        return `${rule.name}: Cascade affecting ${data.affected_entities} entities detected`;
      case 'anomaly_detected':
        return `${rule.name}: Anomaly score ${data.anomaly_score.toFixed(2)} detected`;
      case 'model_prediction':
        return `${rule.name}: Model predicts ${data.predicted_risk} risk with ${(data.confidence * 100).toFixed(0)}% confidence`;
      default:
        return rule.name;
    }
  }

  /**
   * Add listener for alert events
   */
  addListener(callback) {
    this.listeners.push(callback);
  }

  /**
   * Remove listener
   */
  removeListener(callback) {
    this.listeners = this.listeners.filter((cb) => cb !== callback);
  }

  /**
   * Notify all listeners
   */
  notifyListeners(event, data) {
    this.listeners.forEach((callback) => {
      try {
        callback(event, data);
      } catch (error) {
        console.error('Error in alert listener:', error);
      }
    });
  }

  /**
   * Get alert statistics
   */
  async getAlertStatistics() {
    const alerts = await this.getAlerts();
    
    return {
      total: alerts.length,
      active: alerts.filter((a) => !a.acknowledged).length,
      acknowledged: alerts.filter((a) => a.acknowledged).length,
      by_severity: {
        critical: alerts.filter((a) => a.severity === 'critical').length,
        warning: alerts.filter((a) => a.severity === 'warning').length,
        info: alerts.filter((a) => a.severity === 'info').length,
      },
      by_type: {
        threshold_breach: alerts.filter((a) => a.type === 'threshold_breach').length,
        cascade_detected: alerts.filter((a) => a.type === 'cascade_detected').length,
        anomaly_detected: alerts.filter((a) => a.type === 'anomaly_detected').length,
        model_prediction: alerts.filter((a) => a.type === 'model_prediction').length,
      },
    };
  }
}

export default new AlertService();

// Made with Bob
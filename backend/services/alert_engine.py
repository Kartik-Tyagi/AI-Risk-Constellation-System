"""
Alert Engine
Proactive alert system for risk events
"""

import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class AlertEngine:
    """Main alert engine for risk monitoring"""
    
    def __init__(self):
        """Initialize alert engine"""
        self.active_alerts = []
        self.alert_history = []
        self.anomaly_threshold = 2.5  # Standard deviations
        
    def check_threshold_alerts(
        self,
        entity_id: str,
        risk_score: float,
        thresholds: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """
        Check if risk score exceeds thresholds
        
        Args:
            entity_id: Entity identifier
            risk_score: Current risk score
            thresholds: Dictionary of threshold levels
            
        Returns:
            List of triggered alerts
        """
        alerts = []
        
        for level, threshold in thresholds.items():
            if risk_score >= threshold:
                alert = {
                    'type': 'threshold',
                    'level': level,
                    'entity_id': entity_id,
                    'risk_score': risk_score,
                    'threshold': threshold,
                    'message': f"Risk score {risk_score:.2f} exceeds {level} threshold ({threshold:.2f})",
                    'timestamp': datetime.utcnow().isoformat(),
                    'severity': self._get_severity(level)
                }
                alerts.append(alert)
                logger.warning(f"Threshold alert: {alert['message']}")
        
        return alerts
    
    def detect_anomalies(
        self,
        entity_id: str,
        current_value: float,
        historical_values: List[float]
    ) -> Optional[Dict[str, Any]]:
        """
        Detect anomalies using statistical methods
        
        Args:
            entity_id: Entity identifier
            current_value: Current risk value
            historical_values: Historical risk values
            
        Returns:
            Alert if anomaly detected, None otherwise
        """
        if len(historical_values) < 10:
            return None
        
        mean = np.mean(historical_values)
        std = np.std(historical_values)
        
        if std == 0:
            return None
        
        z_score = abs((current_value - mean) / std)
        
        if z_score > self.anomaly_threshold:
            alert = {
                'type': 'anomaly',
                'entity_id': entity_id,
                'current_value': current_value,
                'expected_range': (mean - 2*std, mean + 2*std),
                'z_score': z_score,
                'message': f"Anomalous risk detected for {entity_id}: {current_value:.2f} (z-score: {z_score:.2f})",
                'timestamp': datetime.utcnow().isoformat(),
                'severity': 'high' if z_score > 3 else 'medium'
            }
            logger.warning(f"Anomaly alert: {alert['message']}")
            return alert
        
        return None
    
    def predict_cascade_risk(
        self,
        source_entity: str,
        graph_data: Dict[str, Any],
        risk_scores: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """
        Predict potential cascade effects
        
        Args:
            source_entity: Source entity ID
            graph_data: Graph connectivity data
            risk_scores: Current risk scores
            
        Returns:
            List of cascade alerts
        """
        alerts = []
        
        # Get connected entities
        connected = self._get_connected_entities(source_entity, graph_data)
        
        if not connected:
            return alerts
        
        source_risk = risk_scores.get(source_entity, 0)
        
        # Check if source risk is high enough to trigger cascade
        if source_risk < 70:
            return alerts
        
        # Calculate cascade probability
        for entity_id in connected[:5]:  # Top 5 connected
            entity_risk = risk_scores.get(entity_id, 0)
            cascade_prob = self._calculate_cascade_probability(
                source_risk,
                entity_risk,
                graph_data
            )
            
            if cascade_prob > 0.6:
                alert = {
                    'type': 'cascade',
                    'source_entity': source_entity,
                    'target_entity': entity_id,
                    'cascade_probability': cascade_prob,
                    'source_risk': source_risk,
                    'target_risk': entity_risk,
                    'message': f"High cascade risk from {source_entity} to {entity_id} (prob: {cascade_prob:.2%})",
                    'timestamp': datetime.utcnow().isoformat(),
                    'severity': 'critical' if cascade_prob > 0.8 else 'high'
                }
                alerts.append(alert)
                logger.warning(f"Cascade alert: {alert['message']}")
        
        return alerts
    
    def check_rate_of_change(
        self,
        entity_id: str,
        current_value: float,
        previous_value: float,
        time_delta: timedelta,
        threshold_rate: float = 10.0
    ) -> Optional[Dict[str, Any]]:
        """
        Check if rate of change exceeds threshold
        
        Args:
            entity_id: Entity identifier
            current_value: Current risk value
            previous_value: Previous risk value
            time_delta: Time between measurements
            threshold_rate: Maximum acceptable rate of change per hour
            
        Returns:
            Alert if rate exceeds threshold
        """
        hours = time_delta.total_seconds() / 3600
        if hours == 0:
            return None
        
        rate = abs(current_value - previous_value) / hours
        
        if rate > threshold_rate:
            alert = {
                'type': 'rate_of_change',
                'entity_id': entity_id,
                'current_value': current_value,
                'previous_value': previous_value,
                'rate': rate,
                'threshold_rate': threshold_rate,
                'message': f"Rapid risk change for {entity_id}: {rate:.2f} points/hour",
                'timestamp': datetime.utcnow().isoformat(),
                'severity': 'high' if rate > threshold_rate * 2 else 'medium'
            }
            logger.warning(f"Rate of change alert: {alert['message']}")
            return alert
        
        return None
    
    def check_correlation_alerts(
        self,
        entity_id: str,
        correlated_entities: List[str],
        risk_scores: Dict[str, float],
        correlation_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Check for correlated risk increases
        
        Args:
            entity_id: Entity identifier
            correlated_entities: List of correlated entity IDs
            risk_scores: Current risk scores
            correlation_threshold: Minimum correlation for alert
            
        Returns:
            List of correlation alerts
        """
        alerts = []
        entity_risk = risk_scores.get(entity_id, 0)
        
        if entity_risk < 60:
            return alerts
        
        high_risk_correlated = []
        for corr_id in correlated_entities:
            corr_risk = risk_scores.get(corr_id, 0)
            if corr_risk >= 60:
                high_risk_correlated.append((corr_id, corr_risk))
        
        if len(high_risk_correlated) >= 2:
            alert = {
                'type': 'correlation',
                'entity_id': entity_id,
                'entity_risk': entity_risk,
                'correlated_entities': high_risk_correlated,
                'message': f"Multiple correlated entities showing high risk with {entity_id}",
                'timestamp': datetime.utcnow().isoformat(),
                'severity': 'high'
            }
            alerts.append(alert)
            logger.warning(f"Correlation alert: {alert['message']}")
        
        return alerts
    
    def _get_connected_entities(
        self,
        entity_id: str,
        graph_data: Dict[str, Any]
    ) -> List[str]:
        """Get entities connected to given entity"""
        connected = []
        edges = graph_data.get('edges', [])
        
        for edge in edges:
            if edge[0] == entity_id:
                connected.append(edge[1])
            elif edge[1] == entity_id:
                connected.append(edge[0])
        
        return list(set(connected))
    
    def _calculate_cascade_probability(
        self,
        source_risk: float,
        target_risk: float,
        graph_data: Dict[str, Any]
    ) -> float:
        """Calculate probability of cascade effect"""
        # Simple heuristic: higher source risk and lower target risk = higher cascade prob
        base_prob = (source_risk / 100) * 0.7
        vulnerability = (100 - target_risk) / 100 * 0.3
        return min(base_prob + vulnerability, 1.0)
    
    def _get_severity(self, level: str) -> str:
        """Map threshold level to severity"""
        severity_map = {
            'critical': 'critical',
            'high': 'high',
            'medium': 'medium',
            'low': 'low'
        }
        return severity_map.get(level.lower(), 'medium')
    
    def add_alert(self, alert: Dict[str, Any]) -> str:
        """
        Add alert to active alerts
        
        Args:
            alert: Alert dictionary
            
        Returns:
            Alert ID
        """
        alert_id = f"alert_{len(self.active_alerts) + 1}_{datetime.utcnow().timestamp()}"
        alert['id'] = alert_id
        alert['status'] = 'active'
        alert['acknowledged'] = False
        
        self.active_alerts.append(alert)
        self.alert_history.append(alert.copy())
        
        return alert_id
    
    def acknowledge_alert(self, alert_id: str, user_id: str) -> bool:
        """
        Acknowledge an alert
        
        Args:
            alert_id: Alert identifier
            user_id: User acknowledging the alert
            
        Returns:
            True if successful
        """
        for alert in self.active_alerts:
            if alert['id'] == alert_id:
                alert['acknowledged'] = True
                alert['acknowledged_by'] = user_id
                alert['acknowledged_at'] = datetime.utcnow().isoformat()
                logger.info(f"Alert {alert_id} acknowledged by {user_id}")
                return True
        
        return False
    
    def get_active_alerts(
        self,
        severity: Optional[str] = None,
        entity_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get active alerts with optional filtering
        
        Args:
            severity: Filter by severity level
            entity_id: Filter by entity ID
            
        Returns:
            List of active alerts
        """
        alerts = self.active_alerts
        
        if severity:
            alerts = [a for a in alerts if a.get('severity') == severity]
        
        if entity_id:
            alerts = [a for a in alerts if a.get('entity_id') == entity_id or 
                     a.get('source_entity') == entity_id or 
                     a.get('target_entity') == entity_id]
        
        return alerts
    
    def clear_old_alerts(self, hours: int = 24) -> int:
        """
        Clear alerts older than specified hours
        
        Args:
            hours: Age threshold in hours
            
        Returns:
            Number of alerts cleared
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        initial_count = len(self.active_alerts)
        
        self.active_alerts = [
            alert for alert in self.active_alerts
            if datetime.fromisoformat(alert['timestamp']) > cutoff
        ]
        
        cleared = initial_count - len(self.active_alerts)
        if cleared > 0:
            logger.info(f"Cleared {cleared} old alerts")
        
        return cleared


# Global alert engine instance
_alert_engine = None


def get_alert_engine() -> AlertEngine:
    """Get or create global alert engine instance"""
    global _alert_engine
    if _alert_engine is None:
        _alert_engine = AlertEngine()
    return _alert_engine


# Made with Bob
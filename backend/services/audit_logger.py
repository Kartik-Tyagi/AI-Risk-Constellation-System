"""
Audit Logger
Comprehensive audit trail for risk calculations, user actions, and system events
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of audit events"""
    RISK_CALCULATION = "risk_calculation"
    USER_ACTION = "user_action"
    SYSTEM_EVENT = "system_event"
    DATA_CHANGE = "data_change"
    ALERT_TRIGGERED = "alert_triggered"
    REPORT_GENERATED = "report_generated"
    MODEL_PREDICTION = "model_prediction"
    CONFIGURATION_CHANGE = "configuration_change"
    ACCESS_CONTROL = "access_control"
    ERROR = "error"


class AuditLogger:
    """Main audit logging system"""
    
    def __init__(self, max_entries: int = 100000):
        """
        Initialize audit logger
        
        Args:
            max_entries: Maximum number of entries to keep in memory
        """
        self.audit_trail: List[Dict[str, Any]] = []
        self.max_entries = max_entries
        self.entry_counter = 0
    
    def log_event(
        self,
        event_type: AuditEventType,
        action: str,
        user_id: Optional[str] = None,
        entity_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        severity: str = "info"
    ) -> str:
        """
        Log an audit event
        
        Args:
            event_type: Type of event
            action: Action description
            user_id: User who performed action
            entity_id: Related entity ID
            details: Additional event details
            severity: Event severity (info, warning, error)
            
        Returns:
            Event ID
        """
        self.entry_counter += 1
        event_id = f"AUD-{datetime.utcnow().strftime('%Y%m%d')}-{self.entry_counter:06d}"
        
        event = {
            'event_id': event_id,
            'event_type': event_type.value,
            'action': action,
            'user_id': user_id,
            'entity_id': entity_id,
            'details': details or {},
            'severity': severity,
            'timestamp': datetime.utcnow().isoformat(),
            'ip_address': None,  # Would be populated from request context
            'session_id': None   # Would be populated from session
        }
        
        self.audit_trail.append(event)
        
        # Trim if exceeds max entries
        if len(self.audit_trail) > self.max_entries:
            self.audit_trail = self.audit_trail[-self.max_entries:]
        
        logger.info(f"Audit event logged: {event_id} - {action}")
        return event_id
    
    def log_risk_calculation(
        self,
        entity_id: str,
        risk_score: float,
        model_version: str,
        input_data: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> str:
        """Log a risk calculation"""
        return self.log_event(
            event_type=AuditEventType.RISK_CALCULATION,
            action=f"Risk calculated for {entity_id}",
            user_id=user_id,
            entity_id=entity_id,
            details={
                'risk_score': risk_score,
                'model_version': model_version,
                'input_data': input_data,
                'calculation_time': datetime.utcnow().isoformat()
            }
        )
    
    def log_user_action(
        self,
        user_id: str,
        action: str,
        resource: str,
        success: bool = True,
        details: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log a user action"""
        return self.log_event(
            event_type=AuditEventType.USER_ACTION,
            action=action,
            user_id=user_id,
            details={
                'resource': resource,
                'success': success,
                **(details or {})
            },
            severity='info' if success else 'warning'
        )
    
    def log_system_event(
        self,
        event: str,
        component: str,
        details: Optional[Dict[str, Any]] = None,
        severity: str = "info"
    ) -> str:
        """Log a system event"""
        return self.log_event(
            event_type=AuditEventType.SYSTEM_EVENT,
            action=event,
            details={
                'component': component,
                **(details or {})
            },
            severity=severity
        )
    
    def log_data_change(
        self,
        entity_id: str,
        field: str,
        old_value: Any,
        new_value: Any,
        user_id: Optional[str] = None
    ) -> str:
        """Log a data change"""
        return self.log_event(
            event_type=AuditEventType.DATA_CHANGE,
            action=f"Data changed for {entity_id}",
            user_id=user_id,
            entity_id=entity_id,
            details={
                'field': field,
                'old_value': str(old_value),
                'new_value': str(new_value),
                'change_type': 'update'
            }
        )
    
    def log_alert_triggered(
        self,
        alert_id: str,
        alert_type: str,
        entity_id: Optional[str] = None,
        severity: str = "medium",
        details: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log an alert being triggered"""
        return self.log_event(
            event_type=AuditEventType.ALERT_TRIGGERED,
            action=f"Alert triggered: {alert_type}",
            entity_id=entity_id,
            details={
                'alert_id': alert_id,
                'alert_type': alert_type,
                **(details or {})
            },
            severity=severity
        )
    
    def log_report_generated(
        self,
        report_id: str,
        template_id: str,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log report generation"""
        return self.log_event(
            event_type=AuditEventType.REPORT_GENERATED,
            action=f"Report generated: {report_id}",
            user_id=user_id,
            details={
                'report_id': report_id,
                'template_id': template_id,
                **(details or {})
            }
        )
    
    def log_model_prediction(
        self,
        model_name: str,
        model_version: str,
        input_data: Dict[str, Any],
        prediction: Any,
        confidence: Optional[float] = None
    ) -> str:
        """Log a model prediction"""
        return self.log_event(
            event_type=AuditEventType.MODEL_PREDICTION,
            action=f"Model prediction: {model_name}",
            details={
                'model_name': model_name,
                'model_version': model_version,
                'input_data': input_data,
                'prediction': str(prediction),
                'confidence': confidence
            }
        )
    
    def log_configuration_change(
        self,
        config_key: str,
        old_value: Any,
        new_value: Any,
        user_id: Optional[str] = None
    ) -> str:
        """Log a configuration change"""
        return self.log_event(
            event_type=AuditEventType.CONFIGURATION_CHANGE,
            action=f"Configuration changed: {config_key}",
            user_id=user_id,
            details={
                'config_key': config_key,
                'old_value': str(old_value),
                'new_value': str(new_value)
            },
            severity='warning'
        )
    
    def log_access_control(
        self,
        user_id: str,
        resource: str,
        action: str,
        granted: bool,
        reason: Optional[str] = None
    ) -> str:
        """Log an access control decision"""
        return self.log_event(
            event_type=AuditEventType.ACCESS_CONTROL,
            action=f"Access {'granted' if granted else 'denied'}: {action} on {resource}",
            user_id=user_id,
            details={
                'resource': resource,
                'action': action,
                'granted': granted,
                'reason': reason
            },
            severity='info' if granted else 'warning'
        )
    
    def log_error(
        self,
        error_type: str,
        error_message: str,
        component: str,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log an error"""
        return self.log_event(
            event_type=AuditEventType.ERROR,
            action=f"Error: {error_type}",
            user_id=user_id,
            details={
                'error_type': error_type,
                'error_message': error_message,
                'component': component,
                **(details or {})
            },
            severity='error'
        )
    
    def query_trail(
        self,
        event_type: Optional[AuditEventType] = None,
        user_id: Optional[str] = None,
        entity_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        severity: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Query audit trail with filters
        
        Args:
            event_type: Filter by event type
            user_id: Filter by user ID
            entity_id: Filter by entity ID
            start_time: Start of time range
            end_time: End of time range
            severity: Filter by severity
            limit: Maximum number of results
            
        Returns:
            List of matching audit events
        """
        results = self.audit_trail.copy()
        
        # Apply filters
        if event_type:
            results = [e for e in results if e['event_type'] == event_type.value]
        
        if user_id:
            results = [e for e in results if e['user_id'] == user_id]
        
        if entity_id:
            results = [e for e in results if e['entity_id'] == entity_id]
        
        if severity:
            results = [e for e in results if e['severity'] == severity]
        
        if start_time:
            results = [
                e for e in results
                if datetime.fromisoformat(e['timestamp']) >= start_time
            ]
        
        if end_time:
            results = [
                e for e in results
                if datetime.fromisoformat(e['timestamp']) <= end_time
            ]
        
        # Sort by timestamp (newest first)
        results.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return results[:limit]
    
    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific audit event by ID"""
        for event in self.audit_trail:
            if event['event_id'] == event_id:
                return event
        return None
    
    def get_user_activity(
        self,
        user_id: str,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Get recent activity for a user"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        return self.query_trail(user_id=user_id, start_time=start_time)
    
    def get_entity_history(
        self,
        entity_id: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get history for an entity"""
        start_time = datetime.utcnow() - timedelta(days=days)
        return self.query_trail(entity_id=entity_id, start_time=start_time)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get audit trail statistics"""
        total_events = len(self.audit_trail)
        
        # Count by event type
        by_type = {}
        for event in self.audit_trail:
            event_type = event['event_type']
            by_type[event_type] = by_type.get(event_type, 0) + 1
        
        # Count by severity
        by_severity = {}
        for event in self.audit_trail:
            severity = event['severity']
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        # Recent activity (last 24 hours)
        cutoff = datetime.utcnow() - timedelta(hours=24)
        recent = sum(
            1 for e in self.audit_trail
            if datetime.fromisoformat(e['timestamp']) > cutoff
        )
        
        return {
            'total_events': total_events,
            'by_type': by_type,
            'by_severity': by_severity,
            'recent_24h': recent,
            'oldest_event': self.audit_trail[0]['timestamp'] if self.audit_trail else None,
            'newest_event': self.audit_trail[-1]['timestamp'] if self.audit_trail else None
        }
    
    def export_trail(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        format: str = 'json'
    ) -> Any:
        """
        Export audit trail
        
        Args:
            start_time: Start of time range
            end_time: End of time range
            format: Export format (json, csv)
            
        Returns:
            Exported data
        """
        events = self.query_trail(start_time=start_time, end_time=end_time, limit=len(self.audit_trail))
        
        if format == 'json':
            return json.dumps(events, indent=2)
        
        elif format == 'csv':
            # In production, use csv module or pandas
            return {
                'type': 'csv',
                'placeholder': 'CSV export would happen here',
                'events': events
            }
        
        return events


# Global audit logger instance
_audit_logger = None


def get_audit_logger() -> AuditLogger:
    """Get or create global audit logger instance"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


# Made with Bob
"""
Alert API Routes
Endpoints for alert management
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Any, Optional
import logging

from backend.services.alert_engine import get_alert_engine
from backend.services.alert_rules import get_rule_engine
from backend.services.alert_scheduler import get_scheduler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("")
async def list_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity"),
    entity_id: Optional[str] = Query(None, description="Filter by entity ID"),
    status: Optional[str] = Query(None, description="Filter by status (active/acknowledged)"),
    limit: int = Query(100, ge=1, le=1000)
) -> Dict[str, Any]:
    """
    List alerts with optional filtering
    
    Args:
        severity: Filter by severity level
        entity_id: Filter by entity ID
        status: Filter by status
        limit: Maximum number of alerts to return
        
    Returns:
        List of alerts
    """
    try:
        engine = get_alert_engine()
        alerts = engine.get_active_alerts(severity=severity, entity_id=entity_id)
        
        # Filter by status
        if status == 'acknowledged':
            alerts = [a for a in alerts if a.get('acknowledged', False)]
        elif status == 'active':
            alerts = [a for a in alerts if not a.get('acknowledged', False)]
        
        # Apply limit
        alerts = alerts[:limit]
        
        return {
            'alerts': alerts,
            'total': len(alerts),
            'filters': {
                'severity': severity,
                'entity_id': entity_id,
                'status': status
            }
        }
        
    except Exception as e:
        logger.error(f"Error listing alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{alert_id}")
async def get_alert(alert_id: str) -> Dict[str, Any]:
    """
    Get a specific alert by ID
    
    Args:
        alert_id: Alert identifier
        
    Returns:
        Alert details
    """
    try:
        engine = get_alert_engine()
        
        # Find alert in active alerts
        for alert in engine.active_alerts:
            if alert.get('id') == alert_id:
                return alert
        
        # Check history
        for alert in engine.alert_history:
            if alert.get('id') == alert_id:
                return alert
        
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    user_id: str = Query(..., description="User acknowledging the alert")
) -> Dict[str, Any]:
    """
    Acknowledge an alert
    
    Args:
        alert_id: Alert identifier
        user_id: User ID
        
    Returns:
        Updated alert
    """
    try:
        engine = get_alert_engine()
        
        success = engine.acknowledge_alert(alert_id, user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
        
        # Get updated alert
        for alert in engine.active_alerts:
            if alert.get('id') == alert_id:
                return {
                    'message': 'Alert acknowledged successfully',
                    'alert': alert
                }
        
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging alert {alert_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_alert_history(
    hours: int = Query(24, ge=1, le=168, description="Hours of history to retrieve"),
    severity: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000)
) -> Dict[str, Any]:
    """
    Get alert history
    
    Args:
        hours: Number of hours of history
        severity: Filter by severity
        limit: Maximum number of alerts
        
    Returns:
        Alert history
    """
    try:
        engine = get_alert_engine()
        
        from datetime import datetime, timedelta
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        # Filter history
        history = [
            alert for alert in engine.alert_history
            if datetime.fromisoformat(alert['timestamp']) > cutoff
        ]
        
        if severity:
            history = [a for a in history if a.get('severity') == severity]
        
        history = history[:limit]
        
        return {
            'history': history,
            'total': len(history),
            'hours': hours,
            'severity_filter': severity
        }
        
    except Exception as e:
        logger.error(f"Error getting alert history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rules")
async def create_alert_rule(rule_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new alert rule
    
    Args:
        rule_data: Rule configuration
        
    Returns:
        Created rule information
    """
    try:
        rule_engine = get_rule_engine()
        
        # Validate required fields
        required = ['rule_id', 'name', 'description', 'condition_type', 'condition_params']
        for field in required:
            if field not in rule_data:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required field: {field}"
                )
        
        # Create rule
        success = rule_engine.create_custom_rule(
            rule_id=rule_data['rule_id'],
            name=rule_data['name'],
            description=rule_data['description'],
            condition_type=rule_data['condition_type'],
            condition_params=rule_data['condition_params'],
            priority=rule_data.get('priority', 5)
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to create rule")
        
        # Get created rule
        rule = rule_engine.get_rule(rule_data['rule_id'])
        
        if not rule:
            raise HTTPException(status_code=500, detail="Rule created but not found")
        
        return {
            'message': 'Rule created successfully',
            'rule': {
                'rule_id': rule.rule_id,
                'name': rule.name,
                'description': rule.description,
                'priority': rule.priority,
                'enabled': rule.enabled
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rules")
async def list_alert_rules(
    enabled_only: bool = Query(False, description="Only return enabled rules")
) -> Dict[str, Any]:
    """
    List all alert rules
    
    Args:
        enabled_only: Only return enabled rules
        
    Returns:
        List of rules
    """
    try:
        rule_engine = get_rule_engine()
        rules = rule_engine.list_rules(enabled_only=enabled_only)
        
        return {
            'rules': rules,
            'total': len(rules)
        }
        
    except Exception as e:
        logger.error(f"Error listing rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rules/{rule_id}")
async def get_alert_rule(rule_id: str) -> Dict[str, Any]:
    """
    Get a specific alert rule
    
    Args:
        rule_id: Rule identifier
        
    Returns:
        Rule details
    """
    try:
        rule_engine = get_rule_engine()
        rule = rule_engine.get_rule(rule_id)
        
        if not rule:
            raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")
        
        return {
            'rule_id': rule.rule_id,
            'name': rule.name,
            'description': rule.description,
            'priority': rule.priority,
            'enabled': rule.enabled,
            'trigger_count': rule.trigger_count,
            'last_triggered': rule.last_triggered,
            'created_at': rule.created_at,
            'metadata': rule.metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting rule {rule_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/rules/{rule_id}/enable")
async def enable_alert_rule(rule_id: str) -> Dict[str, Any]:
    """Enable an alert rule"""
    try:
        rule_engine = get_rule_engine()
        success = rule_engine.enable_rule(rule_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")
        
        return {'message': f'Rule {rule_id} enabled successfully'}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enabling rule {rule_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/rules/{rule_id}/disable")
async def disable_alert_rule(rule_id: str) -> Dict[str, Any]:
    """Disable an alert rule"""
    try:
        rule_engine = get_rule_engine()
        success = rule_engine.disable_rule(rule_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")
        
        return {'message': f'Rule {rule_id} disabled successfully'}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling rule {rule_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/rules/{rule_id}")
async def delete_alert_rule(rule_id: str) -> Dict[str, Any]:
    """Delete an alert rule"""
    try:
        rule_engine = get_rule_engine()
        success = rule_engine.remove_rule(rule_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")
        
        return {'message': f'Rule {rule_id} deleted successfully'}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting rule {rule_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_alert_statistics() -> Dict[str, Any]:
    """
    Get alert system statistics
    
    Returns:
        Statistics about alerts, rules, and scheduler
    """
    try:
        engine = get_alert_engine()
        rule_engine = get_rule_engine()
        scheduler = get_scheduler()
        
        return {
            'alerts': {
                'active': len(engine.active_alerts),
                'total_history': len(engine.alert_history)
            },
            'rules': rule_engine.get_statistics(),
            'scheduler': scheduler.get_statistics()
        }
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check")
async def trigger_alert_check(
    entity_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Manually trigger alert check
    
    Args:
        entity_id: Optional entity ID to check
        
    Returns:
        Check results
    """
    try:
        engine = get_alert_engine()
        rule_engine = get_rule_engine()
        
        # Mock data for demonstration
        import random
        test_data = {
            'entity_id': entity_id or 'ENT-001',
            'risk_score': random.uniform(60, 95),
            'previous_risk_score': random.uniform(50, 80),
            'z_score': random.uniform(1, 4),
            'cascade_probability': random.uniform(0.5, 0.9)
        }
        
        # Evaluate rules
        alerts = rule_engine.evaluate_all(test_data)
        
        # Add to engine
        for alert in alerts:
            engine.add_alert(alert)
        
        return {
            'message': 'Alert check completed',
            'alerts_triggered': len(alerts),
            'alerts': alerts
        }
        
    except Exception as e:
        logger.error(f"Error triggering alert check: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Made with Bob
"""
Alert Rules System
Define and evaluate alert rules
"""

from typing import Dict, List, Any, Callable, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AlertRule:
    """Represents a single alert rule"""
    
    def __init__(
        self,
        rule_id: str,
        name: str,
        description: str,
        condition: Callable,
        priority: int = 5,
        enabled: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize alert rule
        
        Args:
            rule_id: Unique rule identifier
            name: Rule name
            description: Rule description
            condition: Function that evaluates the rule
            priority: Rule priority (1-10, 10 is highest)
            enabled: Whether rule is active
            metadata: Additional rule metadata
        """
        self.rule_id = rule_id
        self.name = name
        self.description = description
        self.condition = condition
        self.priority = priority
        self.enabled = enabled
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow().isoformat()
        self.last_triggered = None
        self.trigger_count = 0
    
    def evaluate(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Evaluate rule against data
        
        Args:
            data: Data to evaluate
            
        Returns:
            Alert dict if triggered, None otherwise
        """
        if not self.enabled:
            return None
        
        try:
            result = self.condition(data)
            if result:
                self.last_triggered = datetime.utcnow().isoformat()
                self.trigger_count += 1
                
                alert = {
                    'rule_id': self.rule_id,
                    'rule_name': self.name,
                    'priority': self.priority,
                    'message': result if isinstance(result, str) else self.description,
                    'timestamp': self.last_triggered,
                    'data': data
                }
                return alert
        except Exception as e:
            logger.error(f"Error evaluating rule {self.rule_id}: {e}")
        
        return None


class AlertRuleEngine:
    """Manages and evaluates alert rules"""
    
    def __init__(self):
        """Initialize rule engine"""
        self.rules: Dict[str, AlertRule] = {}
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """Initialize default alert rules"""
        
        # High risk threshold rule
        self.add_rule(AlertRule(
            rule_id='high_risk_threshold',
            name='High Risk Threshold',
            description='Alert when risk score exceeds 80',
            condition=lambda data: data.get('risk_score', 0) > 80,
            priority=9
        ))
        
        # Critical risk threshold rule
        self.add_rule(AlertRule(
            rule_id='critical_risk_threshold',
            name='Critical Risk Threshold',
            description='Alert when risk score exceeds 90',
            condition=lambda data: data.get('risk_score', 0) > 90,
            priority=10
        ))
        
        # Rapid risk increase rule
        self.add_rule(AlertRule(
            rule_id='rapid_risk_increase',
            name='Rapid Risk Increase',
            description='Alert when risk increases by more than 20 points',
            condition=lambda data: (
                data.get('risk_score', 0) - data.get('previous_risk_score', 0) > 20
            ),
            priority=8
        ))
        
        # Multiple entity correlation rule
        self.add_rule(AlertRule(
            rule_id='correlated_high_risk',
            name='Correlated High Risk',
            description='Alert when multiple correlated entities show high risk',
            condition=lambda data: (
                len(data.get('high_risk_correlated', [])) >= 3
            ),
            priority=7
        ))
        
        # Cascade risk rule
        self.add_rule(AlertRule(
            rule_id='cascade_risk',
            name='Cascade Risk',
            description='Alert when cascade probability exceeds 70%',
            condition=lambda data: data.get('cascade_probability', 0) > 0.7,
            priority=9
        ))
        
        # Anomaly detection rule
        self.add_rule(AlertRule(
            rule_id='statistical_anomaly',
            name='Statistical Anomaly',
            description='Alert when value is statistical anomaly',
            condition=lambda data: data.get('z_score', 0) > 3,
            priority=7
        ))
        
        # Liquidity risk rule
        self.add_rule(AlertRule(
            rule_id='low_liquidity',
            name='Low Liquidity',
            description='Alert when liquidity drops below threshold',
            condition=lambda data: data.get('liquidity', 1.0) < 0.3,
            priority=6
        ))
        
        # Concentration risk rule
        self.add_rule(AlertRule(
            rule_id='concentration_risk',
            name='Concentration Risk',
            description='Alert when exposure concentration is too high',
            condition=lambda data: data.get('concentration', 0) > 0.4,
            priority=6
        ))
    
    def add_rule(self, rule: AlertRule) -> bool:
        """
        Add a new rule
        
        Args:
            rule: AlertRule instance
            
        Returns:
            True if successful
        """
        if rule.rule_id in self.rules:
            logger.warning(f"Rule {rule.rule_id} already exists, replacing")
        
        self.rules[rule.rule_id] = rule
        logger.info(f"Added rule: {rule.name} ({rule.rule_id})")
        return True
    
    def remove_rule(self, rule_id: str) -> bool:
        """
        Remove a rule
        
        Args:
            rule_id: Rule identifier
            
        Returns:
            True if successful
        """
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.info(f"Removed rule: {rule_id}")
            return True
        return False
    
    def enable_rule(self, rule_id: str) -> bool:
        """Enable a rule"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = True
            return True
        return False
    
    def disable_rule(self, rule_id: str) -> bool:
        """Disable a rule"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = False
            return True
        return False
    
    def evaluate_all(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Evaluate all rules against data
        
        Args:
            data: Data to evaluate
            
        Returns:
            List of triggered alerts
        """
        alerts = []
        
        # Sort rules by priority (highest first)
        sorted_rules = sorted(
            self.rules.values(),
            key=lambda r: r.priority,
            reverse=True
        )
        
        for rule in sorted_rules:
            alert = rule.evaluate(data)
            if alert:
                alerts.append(alert)
        
        return alerts
    
    def evaluate_rule(
        self,
        rule_id: str,
        data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluate a specific rule
        
        Args:
            rule_id: Rule identifier
            data: Data to evaluate
            
        Returns:
            Alert if triggered
        """
        if rule_id not in self.rules:
            logger.error(f"Rule {rule_id} not found")
            return None
        
        return self.rules[rule_id].evaluate(data)
    
    def get_rule(self, rule_id: str) -> Optional[AlertRule]:
        """Get a rule by ID"""
        return self.rules.get(rule_id)
    
    def list_rules(
        self,
        enabled_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        List all rules
        
        Args:
            enabled_only: Only return enabled rules
            
        Returns:
            List of rule information
        """
        rules = self.rules.values()
        
        if enabled_only:
            rules = [r for r in rules if r.enabled]
        
        return [
            {
                'rule_id': r.rule_id,
                'name': r.name,
                'description': r.description,
                'priority': r.priority,
                'enabled': r.enabled,
                'trigger_count': r.trigger_count,
                'last_triggered': r.last_triggered,
                'created_at': r.created_at
            }
            for r in rules
        ]
    
    def create_custom_rule(
        self,
        rule_id: str,
        name: str,
        description: str,
        condition_type: str,
        condition_params: Dict[str, Any],
        priority: int = 5
    ) -> bool:
        """
        Create a custom rule from parameters
        
        Args:
            rule_id: Unique rule identifier
            name: Rule name
            description: Rule description
            condition_type: Type of condition (threshold, rate, etc.)
            condition_params: Parameters for the condition
            priority: Rule priority
            
        Returns:
            True if successful
        """
        try:
            condition = self._build_condition(condition_type, condition_params)
            
            rule = AlertRule(
                rule_id=rule_id,
                name=name,
                description=description,
                condition=condition,
                priority=priority,
                metadata={'condition_type': condition_type, 'params': condition_params}
            )
            
            return self.add_rule(rule)
        except Exception as e:
            logger.error(f"Error creating custom rule: {e}")
            return False
    
    def _build_condition(
        self,
        condition_type: str,
        params: Dict[str, Any]
    ) -> Callable:
        """Build condition function from type and parameters"""
        
        if condition_type == 'threshold':
            field = params.get('field', 'risk_score')
            operator = params.get('operator', '>')
            value = params.get('value', 0)
            
            if operator == '>':
                return lambda data: data.get(field, 0) > value
            elif operator == '>=':
                return lambda data: data.get(field, 0) >= value
            elif operator == '<':
                return lambda data: data.get(field, 0) < value
            elif operator == '<=':
                return lambda data: data.get(field, 0) <= value
            elif operator == '==':
                return lambda data: data.get(field, 0) == value
        
        elif condition_type == 'rate_of_change':
            field = params.get('field', 'risk_score')
            previous_field = params.get('previous_field', 'previous_risk_score')
            threshold = params.get('threshold', 10)
            
            return lambda data: abs(
                data.get(field, 0) - data.get(previous_field, 0)
            ) > threshold
        
        elif condition_type == 'list_length':
            field = params.get('field', 'items')
            operator = params.get('operator', '>')
            value = params.get('value', 0)
            
            if operator == '>':
                return lambda data: len(data.get(field, [])) > value
            elif operator == '>=':
                return lambda data: len(data.get(field, [])) >= value
        
        # Default: always false
        return lambda data: False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get rule engine statistics"""
        total_rules = len(self.rules)
        enabled_rules = sum(1 for r in self.rules.values() if r.enabled)
        total_triggers = sum(r.trigger_count for r in self.rules.values())
        
        most_triggered = max(
            self.rules.values(),
            key=lambda r: r.trigger_count,
            default=None
        )
        
        return {
            'total_rules': total_rules,
            'enabled_rules': enabled_rules,
            'disabled_rules': total_rules - enabled_rules,
            'total_triggers': total_triggers,
            'most_triggered_rule': {
                'rule_id': most_triggered.rule_id,
                'name': most_triggered.name,
                'trigger_count': most_triggered.trigger_count
            } if most_triggered else None
        }


# Global rule engine instance
_rule_engine = None


def get_rule_engine() -> AlertRuleEngine:
    """Get or create global rule engine instance"""
    global _rule_engine
    if _rule_engine is None:
        _rule_engine = AlertRuleEngine()
    return _rule_engine


# Made with Bob
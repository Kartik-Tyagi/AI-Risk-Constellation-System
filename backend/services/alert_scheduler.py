"""
Alert Scheduler
Background task scheduling for periodic alert checks
"""

import asyncio
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class AlertScheduler:
    """Schedules and executes periodic alert checks"""
    
    def __init__(self):
        """Initialize alert scheduler"""
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.running = False
        self.alert_batch: List[Dict[str, Any]] = []
        self.batch_size = 10
        self.batch_interval = 60  # seconds
        self.last_batch_time = datetime.utcnow()
        
    async def start(self):
        """Start the scheduler"""
        if self.running:
            logger.warning("Scheduler already running")
            return
        
        self.running = True
        logger.info("Alert scheduler started")
        
        # Start background tasks
        asyncio.create_task(self._run_scheduler())
        asyncio.create_task(self._process_batch())
    
    async def stop(self):
        """Stop the scheduler"""
        self.running = False
        logger.info("Alert scheduler stopped")
    
    async def _run_scheduler(self):
        """Main scheduler loop"""
        while self.running:
            try:
                current_time = datetime.utcnow()
                
                # Check each scheduled task
                for task_id, task in list(self.tasks.items()):
                    if not task['enabled']:
                        continue
                    
                    # Check if task should run
                    if self._should_run(task, current_time):
                        await self._execute_task(task_id, task)
                        task['last_run'] = current_time
                        task['run_count'] += 1
                
                # Sleep for a short interval
                await asyncio.sleep(10)
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(10)
    
    async def _process_batch(self):
        """Process batched alerts"""
        while self.running:
            try:
                current_time = datetime.utcnow()
                time_since_batch = (current_time - self.last_batch_time).total_seconds()
                
                # Process batch if interval elapsed or batch is full
                if (time_since_batch >= self.batch_interval or 
                    len(self.alert_batch) >= self.batch_size):
                    
                    if self.alert_batch:
                        await self._deliver_batch()
                        self.alert_batch = []
                        self.last_batch_time = current_time
                
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error in batch processor: {e}")
                await asyncio.sleep(5)
    
    def _should_run(self, task: Dict[str, Any], current_time: datetime) -> bool:
        """Check if task should run"""
        if task['last_run'] is None:
            return True
        
        interval = task['interval']
        time_since_run = (current_time - task['last_run']).total_seconds()
        
        return time_since_run >= interval
    
    async def _execute_task(self, task_id: str, task: Dict[str, Any]):
        """Execute a scheduled task"""
        try:
            logger.debug(f"Executing task: {task_id}")
            
            # Call the task function
            result = await task['function']()
            
            # If result contains alerts, add to batch
            if isinstance(result, list):
                for alert in result:
                    self.add_to_batch(alert)
            elif isinstance(result, dict):
                self.add_to_batch(result)
            
            task['last_result'] = 'success'
            
        except Exception as e:
            logger.error(f"Error executing task {task_id}: {e}")
            task['last_result'] = f'error: {str(e)}'
            task['error_count'] += 1
    
    def schedule_task(
        self,
        task_id: str,
        function: Callable,
        interval: int,
        description: str = "",
        enabled: bool = True
    ) -> bool:
        """
        Schedule a periodic task
        
        Args:
            task_id: Unique task identifier
            function: Async function to execute
            interval: Interval in seconds
            description: Task description
            enabled: Whether task is enabled
            
        Returns:
            True if successful
        """
        if task_id in self.tasks:
            logger.warning(f"Task {task_id} already exists, replacing")
        
        self.tasks[task_id] = {
            'function': function,
            'interval': interval,
            'description': description,
            'enabled': enabled,
            'last_run': None,
            'run_count': 0,
            'error_count': 0,
            'last_result': None,
            'created_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Scheduled task: {task_id} (interval: {interval}s)")
        return True
    
    def unschedule_task(self, task_id: str) -> bool:
        """Unschedule a task"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            logger.info(f"Unscheduled task: {task_id}")
            return True
        return False
    
    def enable_task(self, task_id: str) -> bool:
        """Enable a task"""
        if task_id in self.tasks:
            self.tasks[task_id]['enabled'] = True
            return True
        return False
    
    def disable_task(self, task_id: str) -> bool:
        """Disable a task"""
        if task_id in self.tasks:
            self.tasks[task_id]['enabled'] = False
            return True
        return False
    
    def add_to_batch(self, alert: Dict[str, Any]):
        """Add alert to batch for delivery"""
        self.alert_batch.append(alert)
        logger.debug(f"Added alert to batch (size: {len(self.alert_batch)})")
    
    async def _deliver_batch(self):
        """Deliver batched alerts"""
        if not self.alert_batch:
            return
        
        logger.info(f"Delivering batch of {len(self.alert_batch)} alerts")
        
        try:
            # Group alerts by severity
            grouped = defaultdict(list)
            for alert in self.alert_batch:
                severity = alert.get('severity', 'medium')
                grouped[severity].append(alert)
            
            # Log batch summary
            summary = {
                'total': len(self.alert_batch),
                'by_severity': {k: len(v) for k, v in grouped.items()},
                'timestamp': datetime.utcnow().isoformat()
            }
            logger.info(f"Alert batch summary: {summary}")
            
            # In production, this would send to notification service
            # For now, just log
            
        except Exception as e:
            logger.error(f"Error delivering batch: {e}")
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a task"""
        if task_id not in self.tasks:
            return None
        
        task = self.tasks[task_id]
        return {
            'task_id': task_id,
            'description': task['description'],
            'interval': task['interval'],
            'enabled': task['enabled'],
            'last_run': task['last_run'].isoformat() if task['last_run'] else None,
            'run_count': task['run_count'],
            'error_count': task['error_count'],
            'last_result': task['last_result'],
            'created_at': task['created_at']
        }
    
    def list_tasks(self) -> List[Dict[str, Any]]:
        """List all scheduled tasks"""
        tasks = []
        for task_id in self.tasks.keys():
            status = self.get_task_status(task_id)
            if status:
                tasks.append(status)
        return tasks
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get scheduler statistics"""
        total_tasks = len(self.tasks)
        enabled_tasks = sum(1 for t in self.tasks.values() if t['enabled'])
        total_runs = sum(t['run_count'] for t in self.tasks.values())
        total_errors = sum(t['error_count'] for t in self.tasks.values())
        
        return {
            'running': self.running,
            'total_tasks': total_tasks,
            'enabled_tasks': enabled_tasks,
            'disabled_tasks': total_tasks - enabled_tasks,
            'total_runs': total_runs,
            'total_errors': total_errors,
            'batch_size': len(self.alert_batch),
            'batch_limit': self.batch_size
        }


class PeriodicAlertChecker:
    """Performs periodic alert checks"""
    
    def __init__(self, alert_engine, rule_engine):
        """
        Initialize periodic checker
        
        Args:
            alert_engine: AlertEngine instance
            rule_engine: AlertRuleEngine instance
        """
        self.alert_engine = alert_engine
        self.rule_engine = rule_engine
    
    async def check_all_entities(self) -> List[Dict[str, Any]]:
        """Check all entities for alerts"""
        alerts = []
        
        try:
            # Mock: In production, fetch from database
            entities = self._get_mock_entities()
            
            for entity in entities:
                # Check thresholds
                threshold_alerts = self.alert_engine.check_threshold_alerts(
                    entity['id'],
                    entity['risk_score'],
                    {'high': 75, 'critical': 90}
                )
                alerts.extend(threshold_alerts)
                
                # Check anomalies
                if 'historical_scores' in entity:
                    anomaly_alert = self.alert_engine.detect_anomalies(
                        entity['id'],
                        entity['risk_score'],
                        entity['historical_scores']
                    )
                    if anomaly_alert:
                        alerts.append(anomaly_alert)
                
                # Evaluate rules
                rule_alerts = self.rule_engine.evaluate_all(entity)
                alerts.extend(rule_alerts)
            
            # Add alerts to engine
            for alert in alerts:
                self.alert_engine.add_alert(alert)
            
            logger.info(f"Periodic check found {len(alerts)} alerts")
            
        except Exception as e:
            logger.error(f"Error in periodic check: {e}")
        
        return alerts
    
    async def check_cascade_risks(self) -> List[Dict[str, Any]]:
        """Check for cascade risks"""
        alerts = []
        
        try:
            # Mock: In production, fetch from database
            graph_data = self._get_mock_graph()
            risk_scores = self._get_mock_risk_scores()
            
            high_risk_entities = [
                eid for eid, score in risk_scores.items() if score > 70
            ]
            
            for entity_id in high_risk_entities:
                cascade_alerts = self.alert_engine.predict_cascade_risk(
                    entity_id,
                    graph_data,
                    risk_scores
                )
                alerts.extend(cascade_alerts)
            
            for alert in alerts:
                self.alert_engine.add_alert(alert)
            
            logger.info(f"Cascade check found {len(alerts)} alerts")
            
        except Exception as e:
            logger.error(f"Error in cascade check: {e}")
        
        return alerts
    
    def _get_mock_entities(self) -> List[Dict[str, Any]]:
        """Get mock entity data"""
        import random
        return [
            {
                'id': f'ENT-{i:03d}',
                'risk_score': random.uniform(30, 95),
                'previous_risk_score': random.uniform(30, 90),
                'historical_scores': [random.uniform(30, 90) for _ in range(20)]
            }
            for i in range(10)
        ]
    
    def _get_mock_graph(self) -> Dict[str, Any]:
        """Get mock graph data"""
        return {
            'nodes': [f'ENT-{i:03d}' for i in range(10)],
            'edges': [
                (f'ENT-{i:03d}', f'ENT-{j:03d}')
                for i in range(10) for j in range(i+1, min(i+3, 10))
            ]
        }
    
    def _get_mock_risk_scores(self) -> Dict[str, float]:
        """Get mock risk scores"""
        import random
        return {
            f'ENT-{i:03d}': random.uniform(30, 95)
            for i in range(10)
        }


# Global scheduler instance
_scheduler = None


def get_scheduler() -> AlertScheduler:
    """Get or create global scheduler instance"""
    global _scheduler
    if _scheduler is None:
        _scheduler = AlertScheduler()
    return _scheduler


# Made with Bob
"""
Update Publisher
Publishes updates to WebSocket clients with filtering and rate limiting
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum

from backend.api.websocket.risk_updates import (
    get_risk_update_handler,
    UpdateType
)

logger = logging.getLogger(__name__)


class PublishPriority(Enum):
    """Update priority levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class UpdatePublisher:
    """Publishes updates to WebSocket clients with filtering and rate limiting"""
    
    def __init__(self):
        self.update_handler = get_risk_update_handler()
        
        # Rate limiting: topic -> last publish time
        self.last_publish_time: Dict[str, datetime] = {}
        
        # Rate limits by update type (seconds)
        self.rate_limits = {
            UpdateType.RISK_CALCULATION: 5,
            UpdateType.MARKET_DATA: 1,
            UpdateType.ALERT: 0,  # No rate limit for alerts
            UpdateType.PORTFOLIO_UPDATE: 10,
            UpdateType.GRAPH_UPDATE: 30
        }
        
        # Update queue: priority -> list of updates
        self.update_queue: Dict[PublishPriority, List[Dict[str, Any]]] = {
            priority: [] for priority in PublishPriority
        }
        
        # Processing flag
        self.processing = False
        self.process_task: Optional[asyncio.Task] = None
    
    async def publish_risk_update(
        self,
        entity_id: str,
        risk_data: Dict[str, Any],
        priority: PublishPriority = PublishPriority.MEDIUM,
        client_ids: Optional[List[str]] = None
    ):
        """
        Publish risk calculation update
        
        Args:
            entity_id: Entity ID
            risk_data: Risk data
            priority: Update priority
            client_ids: Optional specific clients
        """
        update = {
            'type': UpdateType.RISK_CALCULATION,
            'entity_id': entity_id,
            'data': risk_data,
            'client_ids': client_ids,
            'timestamp': datetime.now()
        }
        
        await self._queue_update(update, priority)
    
    async def publish_market_update(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        priority: PublishPriority = PublishPriority.LOW
    ):
        """
        Publish market data update
        
        Args:
            symbol: Market symbol
            market_data: Market data
            priority: Update priority
        """
        update = {
            'type': UpdateType.MARKET_DATA,
            'symbol': symbol,
            'data': market_data,
            'timestamp': datetime.now()
        }
        
        await self._queue_update(update, priority)
    
    async def publish_alert(
        self,
        alert_type: str,
        severity: str,
        message: str,
        entity_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Publish alert (always high priority, no rate limiting)
        
        Args:
            alert_type: Alert type
            severity: Alert severity
            message: Alert message
            entity_id: Optional entity ID
            metadata: Optional metadata
        """
        update = {
            'type': UpdateType.ALERT,
            'alert_type': alert_type,
            'severity': severity,
            'message': message,
            'entity_id': entity_id,
            'metadata': metadata,
            'timestamp': datetime.now()
        }
        
        # Alerts bypass queue and are sent immediately
        await self.update_handler.send_alert(
            alert_type,
            severity,
            message,
            entity_id,
            metadata
        )
    
    async def publish_portfolio_update(
        self,
        portfolio_id: str,
        update_data: Dict[str, Any],
        priority: PublishPriority = PublishPriority.MEDIUM,
        client_ids: Optional[List[str]] = None
    ):
        """
        Publish portfolio update
        
        Args:
            portfolio_id: Portfolio ID
            update_data: Update data
            priority: Update priority
            client_ids: Optional specific clients
        """
        update = {
            'type': UpdateType.PORTFOLIO_UPDATE,
            'portfolio_id': portfolio_id,
            'data': update_data,
            'client_ids': client_ids,
            'timestamp': datetime.now()
        }
        
        await self._queue_update(update, priority)
    
    async def publish_graph_update(
        self,
        update_type: str,
        graph_data: Dict[str, Any],
        priority: PublishPriority = PublishPriority.LOW
    ):
        """
        Publish graph update
        
        Args:
            update_type: Graph update type
            graph_data: Graph data
            priority: Update priority
        """
        update = {
            'type': UpdateType.GRAPH_UPDATE,
            'update_type': update_type,
            'data': graph_data,
            'timestamp': datetime.now()
        }
        
        await self._queue_update(update, priority)
    
    async def _queue_update(
        self,
        update: Dict[str, Any],
        priority: PublishPriority
    ):
        """
        Queue update for processing
        
        Args:
            update: Update data
            priority: Update priority
        """
        self.update_queue[priority].append(update)
        
        # Start processing if not already running
        if not self.processing:
            await self.start_processing()
    
    async def start_processing(self):
        """Start processing update queue"""
        if self.processing:
            return
        
        self.processing = True
        self.process_task = asyncio.create_task(self._process_queue())
        logger.info("Started update publisher processing")
    
    async def stop_processing(self):
        """Stop processing update queue"""
        self.processing = False
        if self.process_task:
            self.process_task.cancel()
            try:
                await self.process_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped update publisher processing")
    
    async def _process_queue(self):
        """Process update queue"""
        while self.processing:
            try:
                # Process updates by priority (highest first)
                for priority in sorted(PublishPriority, key=lambda p: p.value, reverse=True):
                    while self.update_queue[priority]:
                        update = self.update_queue[priority].pop(0)
                        await self._publish_update(update)
                
                # Sleep briefly before next iteration
                await asyncio.sleep(0.1)
            
            except Exception as e:
                logger.error(f"Error processing update queue: {e}")
                await asyncio.sleep(1)
    
    async def _publish_update(self, update: Dict[str, Any]):
        """
        Publish single update with rate limiting
        
        Args:
            update: Update to publish
        """
        update_type = update['type']
        
        # Check rate limit
        if not self._check_rate_limit(update):
            # Re-queue if rate limited
            self.update_queue[PublishPriority.LOW].append(update)
            return
        
        # Publish based on type
        try:
            if update_type == UpdateType.RISK_CALCULATION:
                await self.update_handler.send_risk_calculation_update(
                    update['entity_id'],
                    update['data'],
                    update.get('client_ids')
                )
            
            elif update_type == UpdateType.MARKET_DATA:
                await self.update_handler.send_market_data_update(
                    update['symbol'],
                    update['data']
                )
            
            elif update_type == UpdateType.PORTFOLIO_UPDATE:
                await self.update_handler.send_portfolio_update(
                    update['portfolio_id'],
                    update['data'],
                    update.get('client_ids')
                )
            
            elif update_type == UpdateType.GRAPH_UPDATE:
                await self.update_handler.send_graph_update(
                    update['update_type'],
                    update['data']
                )
            
            # Update last publish time
            self._update_rate_limit(update)
        
        except Exception as e:
            logger.error(f"Failed to publish update: {e}")
    
    def _check_rate_limit(self, update: Dict[str, Any]) -> bool:
        """
        Check if update can be published based on rate limit
        
        Args:
            update: Update to check
            
        Returns:
            True if can publish, False otherwise
        """
        update_type = update['type']
        rate_limit = self.rate_limits.get(update_type, 0)
        
        if rate_limit == 0:
            return True  # No rate limit
        
        # Build rate limit key
        key = self._get_rate_limit_key(update)
        
        if key not in self.last_publish_time:
            return True
        
        # Check time since last publish
        time_since_last = datetime.now() - self.last_publish_time[key]
        return time_since_last.total_seconds() >= rate_limit
    
    def _update_rate_limit(self, update: Dict[str, Any]):
        """
        Update rate limit tracking
        
        Args:
            update: Published update
        """
        key = self._get_rate_limit_key(update)
        self.last_publish_time[key] = datetime.now()
    
    def _get_rate_limit_key(self, update: Dict[str, Any]) -> str:
        """
        Get rate limit key for update
        
        Args:
            update: Update
            
        Returns:
            Rate limit key
        """
        update_type = update['type']
        
        if update_type == UpdateType.RISK_CALCULATION:
            return f"risk:{update['entity_id']}"
        elif update_type == UpdateType.MARKET_DATA:
            return f"market:{update['symbol']}"
        elif update_type == UpdateType.PORTFOLIO_UPDATE:
            return f"portfolio:{update['portfolio_id']}"
        elif update_type == UpdateType.GRAPH_UPDATE:
            return f"graph:{update['update_type']}"
        else:
            return str(update_type)
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """
        Get queue statistics
        
        Returns:
            Queue statistics
        """
        return {
            'processing': self.processing,
            'queue_sizes': {
                priority.name: len(updates)
                for priority, updates in self.update_queue.items()
            },
            'total_queued': sum(len(updates) for updates in self.update_queue.values()),
            'rate_limit_keys': len(self.last_publish_time)
        }


# Global publisher instance
update_publisher = UpdatePublisher()


def get_update_publisher() -> UpdatePublisher:
    """Get update publisher instance"""
    return update_publisher

# Made with Bob

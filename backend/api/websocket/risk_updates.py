"""
Risk Updates WebSocket Handler
Handles real-time risk calculation updates, market data, and alerts
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

from backend.api.websocket.connection_manager import get_connection_manager

logger = logging.getLogger(__name__)


class UpdateType(Enum):
    """Types of updates"""
    RISK_CALCULATION = "risk_calculation"
    MARKET_DATA = "market_data"
    ALERT = "alert"
    PORTFOLIO_UPDATE = "portfolio_update"
    GRAPH_UPDATE = "graph_update"


class RiskUpdateHandler:
    """Handles real-time risk updates"""
    
    def __init__(self):
        self.connection_manager = get_connection_manager()
    
    async def send_risk_calculation_update(
        self,
        entity_id: str,
        risk_data: Dict[str, Any],
        client_ids: Optional[List[str]] = None
    ):
        """
        Send risk calculation update
        
        Args:
            entity_id: Entity ID
            risk_data: Risk calculation data
            client_ids: Optional list of specific clients to notify
        """
        message = {
            'type': UpdateType.RISK_CALCULATION.value,
            'timestamp': datetime.now().isoformat(),
            'entity_id': entity_id,
            'data': risk_data
        }
        
        if client_ids:
            await self.connection_manager.broadcast_to_clients(message, client_ids)
        else:
            # Broadcast to all clients subscribed to this entity
            topic = f"risk:{entity_id}"
            await self.connection_manager.broadcast(message, topic)
        
        logger.info(f"Sent risk calculation update for entity {entity_id}")
    
    async def send_market_data_update(
        self,
        symbol: str,
        market_data: Dict[str, Any]
    ):
        """
        Send market data update
        
        Args:
            symbol: Market symbol
            market_data: Market data
        """
        message = {
            'type': UpdateType.MARKET_DATA.value,
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'data': market_data
        }
        
        # Broadcast to clients subscribed to this symbol
        topic = f"market:{symbol}"
        await self.connection_manager.broadcast(message, topic)
        
        logger.info(f"Sent market data update for {symbol}")
    
    async def send_alert(
        self,
        alert_type: str,
        severity: str,
        message_text: str,
        entity_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Send alert notification
        
        Args:
            alert_type: Type of alert
            severity: Alert severity (low/medium/high/critical)
            message_text: Alert message
            entity_id: Optional entity ID
            metadata: Optional additional metadata
        """
        message = {
            'type': UpdateType.ALERT.value,
            'timestamp': datetime.now().isoformat(),
            'alert_type': alert_type,
            'severity': severity,
            'message': message_text,
            'entity_id': entity_id,
            'metadata': metadata or {}
        }
        
        # Broadcast to all clients (alerts are important)
        await self.connection_manager.broadcast(message)
        
        logger.warning(f"Sent alert: {alert_type} - {severity} - {message_text}")
    
    async def send_portfolio_update(
        self,
        portfolio_id: str,
        update_data: Dict[str, Any],
        client_ids: Optional[List[str]] = None
    ):
        """
        Send portfolio update
        
        Args:
            portfolio_id: Portfolio ID
            update_data: Portfolio update data
            client_ids: Optional list of specific clients to notify
        """
        message = {
            'type': UpdateType.PORTFOLIO_UPDATE.value,
            'timestamp': datetime.now().isoformat(),
            'portfolio_id': portfolio_id,
            'data': update_data
        }
        
        if client_ids:
            await self.connection_manager.broadcast_to_clients(message, client_ids)
        else:
            # Broadcast to clients subscribed to this portfolio
            topic = f"portfolio:{portfolio_id}"
            await self.connection_manager.broadcast(message, topic)
        
        logger.info(f"Sent portfolio update for {portfolio_id}")
    
    async def send_graph_update(
        self,
        update_type: str,
        graph_data: Dict[str, Any]
    ):
        """
        Send graph/constellation update
        
        Args:
            update_type: Type of graph update
            graph_data: Graph data
        """
        message = {
            'type': UpdateType.GRAPH_UPDATE.value,
            'timestamp': datetime.now().isoformat(),
            'update_type': update_type,
            'data': graph_data
        }
        
        # Broadcast to clients subscribed to graph updates
        topic = "graph:updates"
        await self.connection_manager.broadcast(message, topic)
        
        logger.info(f"Sent graph update: {update_type}")
    
    async def send_batch_updates(
        self,
        updates: List[Dict[str, Any]]
    ):
        """
        Send multiple updates in batch
        
        Args:
            updates: List of update messages
        """
        for update in updates:
            update_type = update.get('type')
            
            if update_type == UpdateType.RISK_CALCULATION.value:
                await self.send_risk_calculation_update(
                    update['entity_id'],
                    update['data'],
                    update.get('client_ids')
                )
            elif update_type == UpdateType.MARKET_DATA.value:
                await self.send_market_data_update(
                    update['symbol'],
                    update['data']
                )
            elif update_type == UpdateType.ALERT.value:
                await self.send_alert(
                    update['alert_type'],
                    update['severity'],
                    update['message'],
                    update.get('entity_id'),
                    update.get('metadata')
                )
            elif update_type == UpdateType.PORTFOLIO_UPDATE.value:
                await self.send_portfolio_update(
                    update['portfolio_id'],
                    update['data'],
                    update.get('client_ids')
                )
            elif update_type == UpdateType.GRAPH_UPDATE.value:
                await self.send_graph_update(
                    update['update_type'],
                    update['data']
                )


class MarketDataStreamer:
    """Streams market data updates"""
    
    def __init__(self, update_handler: RiskUpdateHandler):
        self.update_handler = update_handler
        self.streaming = False
        self.stream_task: Optional[asyncio.Task] = None
    
    async def start_streaming(self, symbols: List[str], interval: int = 5):
        """
        Start streaming market data
        
        Args:
            symbols: List of symbols to stream
            interval: Update interval in seconds
        """
        self.streaming = True
        self.stream_task = asyncio.create_task(
            self._stream_loop(symbols, interval)
        )
        logger.info(f"Started market data streaming for {len(symbols)} symbols")
    
    async def stop_streaming(self):
        """Stop streaming market data"""
        self.streaming = False
        if self.stream_task:
            self.stream_task.cancel()
            try:
                await self.stream_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped market data streaming")
    
    async def _stream_loop(self, symbols: List[str], interval: int):
        """
        Streaming loop
        
        Args:
            symbols: Symbols to stream
            interval: Update interval
        """
        while self.streaming:
            try:
                # TODO: Fetch actual market data
                for symbol in symbols:
                    market_data = {
                        'price': 0.0,  # Placeholder
                        'volume': 0,
                        'change': 0.0
                    }
                    await self.update_handler.send_market_data_update(
                        symbol,
                        market_data
                    )
                
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Error in market data streaming: {e}")
                await asyncio.sleep(interval)


class RiskMonitor:
    """Monitors risk levels and sends alerts"""
    
    def __init__(self, update_handler: RiskUpdateHandler):
        self.update_handler = update_handler
        self.monitoring = False
        self.monitor_task: Optional[asyncio.Task] = None
        self.thresholds = {
            'critical': 90,
            'high': 75,
            'medium': 50,
            'low': 25
        }
    
    async def start_monitoring(self, entities: List[str], interval: int = 60):
        """
        Start risk monitoring
        
        Args:
            entities: List of entity IDs to monitor
            interval: Check interval in seconds
        """
        self.monitoring = True
        self.monitor_task = asyncio.create_task(
            self._monitor_loop(entities, interval)
        )
        logger.info(f"Started risk monitoring for {len(entities)} entities")
    
    async def stop_monitoring(self):
        """Stop risk monitoring"""
        self.monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped risk monitoring")
    
    async def _monitor_loop(self, entities: List[str], interval: int):
        """
        Monitoring loop
        
        Args:
            entities: Entities to monitor
            interval: Check interval
        """
        while self.monitoring:
            try:
                # TODO: Check actual risk levels
                for entity_id in entities:
                    # Placeholder risk check
                    risk_score = 0.0  # Would fetch from database/cache
                    
                    # Check thresholds and send alerts
                    if risk_score >= self.thresholds['critical']:
                        await self.update_handler.send_alert(
                            'risk_threshold',
                            'critical',
                            f"Critical risk level for entity {entity_id}",
                            entity_id
                        )
                
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Error in risk monitoring: {e}")
                await asyncio.sleep(interval)


# Global instances
risk_update_handler = RiskUpdateHandler()
market_data_streamer = MarketDataStreamer(risk_update_handler)
risk_monitor = RiskMonitor(risk_update_handler)


def get_risk_update_handler() -> RiskUpdateHandler:
    """Get risk update handler instance"""
    return risk_update_handler


def get_market_data_streamer() -> MarketDataStreamer:
    """Get market data streamer instance"""
    return market_data_streamer


def get_risk_monitor() -> RiskMonitor:
    """Get risk monitor instance"""
    return risk_monitor

# Made with Bob

"""
WebSocket Connection Manager
Manages WebSocket connections, client tracking, and broadcasting
"""

import logging
import asyncio
from typing import Dict, Set, List, Optional, Any
from datetime import datetime
import json

try:
    from fastapi import WebSocket, WebSocketDisconnect
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    WebSocket = Any
    WebSocketDisconnect = Exception

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and broadcasting"""
    
    def __init__(self):
        # Active connections: client_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}
        
        # Client subscriptions: client_id -> Set of subscription topics
        self.subscriptions: Dict[str, Set[str]] = {}
        
        # Connection metadata: client_id -> metadata dict
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()
    
    async def connect(
        self,
        websocket: WebSocket,
        client_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Accept and register a new WebSocket connection
        
        Args:
            websocket: WebSocket connection
            client_id: Unique client identifier
            metadata: Optional connection metadata
        """
        await websocket.accept()
        
        async with self._lock:
            self.active_connections[client_id] = websocket
            self.subscriptions[client_id] = set()
            self.connection_metadata[client_id] = metadata or {}
            self.connection_metadata[client_id]['connected_at'] = datetime.now().isoformat()
        
        logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")
    
    async def disconnect(self, client_id: str):
        """
        Remove a client connection
        
        Args:
            client_id: Client identifier
        """
        async with self._lock:
            if client_id in self.active_connections:
                del self.active_connections[client_id]
            if client_id in self.subscriptions:
                del self.subscriptions[client_id]
            if client_id in self.connection_metadata:
                del self.connection_metadata[client_id]
        
        logger.info(f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}")
    
    async def subscribe(self, client_id: str, topics: List[str]):
        """
        Subscribe client to topics
        
        Args:
            client_id: Client identifier
            topics: List of topics to subscribe to
        """
        async with self._lock:
            if client_id in self.subscriptions:
                self.subscriptions[client_id].update(topics)
                logger.info(f"Client {client_id} subscribed to: {topics}")
    
    async def unsubscribe(self, client_id: str, topics: List[str]):
        """
        Unsubscribe client from topics
        
        Args:
            client_id: Client identifier
            topics: List of topics to unsubscribe from
        """
        async with self._lock:
            if client_id in self.subscriptions:
                self.subscriptions[client_id].difference_update(topics)
                logger.info(f"Client {client_id} unsubscribed from: {topics}")
    
    async def send_personal_message(self, message: Dict[str, Any], client_id: str):
        """
        Send message to a specific client
        
        Args:
            message: Message to send
            client_id: Target client identifier
        """
        if client_id in self.active_connections:
            try:
                websocket = self.active_connections[client_id]
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message to {client_id}: {e}")
                await self.disconnect(client_id)
    
    async def broadcast(self, message: Dict[str, Any], topic: Optional[str] = None):
        """
        Broadcast message to all clients or clients subscribed to a topic
        
        Args:
            message: Message to broadcast
            topic: Optional topic filter
        """
        disconnected_clients = []
        
        for client_id, websocket in self.active_connections.items():
            # Check if client is subscribed to topic
            if topic and client_id in self.subscriptions:
                if topic not in self.subscriptions[client_id]:
                    continue
            
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to broadcast to {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            await self.disconnect(client_id)
    
    async def broadcast_to_clients(
        self,
        message: Dict[str, Any],
        client_ids: List[str]
    ):
        """
        Broadcast message to specific clients
        
        Args:
            message: Message to broadcast
            client_ids: List of target client identifiers
        """
        for client_id in client_ids:
            await self.send_personal_message(message, client_id)
    
    def get_active_connections(self) -> List[str]:
        """
        Get list of active client IDs
        
        Returns:
            List of active client identifiers
        """
        return list(self.active_connections.keys())
    
    def get_client_subscriptions(self, client_id: str) -> Set[str]:
        """
        Get client's subscriptions
        
        Args:
            client_id: Client identifier
            
        Returns:
            Set of subscribed topics
        """
        return self.subscriptions.get(client_id, set())
    
    def get_connection_count(self) -> int:
        """
        Get number of active connections
        
        Returns:
            Number of active connections
        """
        return len(self.active_connections)
    
    def get_topic_subscribers(self, topic: str) -> List[str]:
        """
        Get clients subscribed to a topic
        
        Args:
            topic: Topic name
            
        Returns:
            List of client identifiers
        """
        subscribers = []
        for client_id, topics in self.subscriptions.items():
            if topic in topics:
                subscribers.append(client_id)
        return subscribers
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """
        Get connection statistics
        
        Returns:
            Dictionary with connection statistics
        """
        topic_counts = {}
        for topics in self.subscriptions.values():
            for topic in topics:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        return {
            'total_connections': len(self.active_connections),
            'total_subscriptions': sum(len(topics) for topics in self.subscriptions.values()),
            'topic_subscriber_counts': topic_counts,
            'clients': list(self.active_connections.keys())
        }


# Global connection manager instance
connection_manager = ConnectionManager()


def get_connection_manager() -> ConnectionManager:
    """
    Get the global connection manager instance
    
    Returns:
        ConnectionManager instance
    """
    return connection_manager

# Made with Bob

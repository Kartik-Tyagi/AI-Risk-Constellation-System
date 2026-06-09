"""
WebSocket Routes
WebSocket endpoints for real-time updates
"""

import logging
import json
from typing import Optional, Dict, Any

try:
    from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    APIRouter = None
    WebSocket = Any
    WebSocketDisconnect = Exception

from backend.api.websocket.connection_manager import get_connection_manager
from backend.api.websocket.risk_updates import get_risk_update_handler

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str,
    token: Optional[str] = Query(None, description="Authentication token")
):
    """
    Main WebSocket endpoint
    
    Args:
        websocket: WebSocket connection
        client_id: Unique client identifier
        token: Optional authentication token
    """
    connection_manager = get_connection_manager()
    
    # TODO: Implement authentication
    # if token:
    #     authenticated = await authenticate_token(token)
    #     if not authenticated:
    #         await websocket.close(code=1008, reason="Authentication failed")
    #         return
    
    # Accept connection
    await connection_manager.connect(
        websocket,
        client_id,
        metadata={'token': token}
    )
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                await handle_client_message(client_id, message, connection_manager)
            except json.JSONDecodeError:
                await connection_manager.send_personal_message(
                    {
                        'type': 'error',
                        'message': 'Invalid JSON format'
                    },
                    client_id
                )
    
    except WebSocketDisconnect:
        await connection_manager.disconnect(client_id)
        logger.info(f"Client {client_id} disconnected")
    
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        await connection_manager.disconnect(client_id)


async def handle_client_message(
    client_id: str,
    message: Dict[str, Any],
    connection_manager
):
    """
    Handle messages from client
    
    Args:
        client_id: Client identifier
        message: Message from client
        connection_manager: Connection manager instance
    """
    message_type = message.get('type')
    
    if message_type == 'subscribe':
        # Subscribe to topics
        topics = message.get('topics', [])
        await connection_manager.subscribe(client_id, topics)
        await connection_manager.send_personal_message(
            {
                'type': 'subscription_confirmed',
                'topics': topics
            },
            client_id
        )
    
    elif message_type == 'unsubscribe':
        # Unsubscribe from topics
        topics = message.get('topics', [])
        await connection_manager.unsubscribe(client_id, topics)
        await connection_manager.send_personal_message(
            {
                'type': 'unsubscription_confirmed',
                'topics': topics
            },
            client_id
        )
    
    elif message_type == 'ping':
        # Respond to ping
        await connection_manager.send_personal_message(
            {
                'type': 'pong',
                'timestamp': message.get('timestamp')
            },
            client_id
        )
    
    elif message_type == 'get_subscriptions':
        # Get current subscriptions
        subscriptions = connection_manager.get_client_subscriptions(client_id)
        await connection_manager.send_personal_message(
            {
                'type': 'subscriptions',
                'topics': list(subscriptions)
            },
            client_id
        )
    
    else:
        # Unknown message type
        await connection_manager.send_personal_message(
            {
                'type': 'error',
                'message': f'Unknown message type: {message_type}'
            },
            client_id
        )


@router.websocket("/ws/risk/{entity_id}")
async def risk_websocket(
    websocket: WebSocket,
    entity_id: str,
    client_id: str = Query(..., description="Client identifier")
):
    """
    WebSocket endpoint for specific entity risk updates
    
    Args:
        websocket: WebSocket connection
        entity_id: Entity ID to monitor
        client_id: Client identifier
    """
    connection_manager = get_connection_manager()
    
    # Accept connection
    await connection_manager.connect(
        websocket,
        client_id,
        metadata={'entity_id': entity_id}
    )
    
    # Auto-subscribe to entity risk updates
    await connection_manager.subscribe(client_id, [f"risk:{entity_id}"])
    
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                if message.get('type') == 'ping':
                    await connection_manager.send_personal_message(
                        {'type': 'pong'},
                        client_id
                    )
            except json.JSONDecodeError:
                pass
    
    except WebSocketDisconnect:
        await connection_manager.disconnect(client_id)
        logger.info(f"Risk WebSocket disconnected for entity {entity_id}")
    
    except Exception as e:
        logger.error(f"Risk WebSocket error: {e}")
        await connection_manager.disconnect(client_id)


@router.websocket("/ws/portfolio/{portfolio_id}")
async def portfolio_websocket(
    websocket: WebSocket,
    portfolio_id: str,
    client_id: str = Query(..., description="Client identifier")
):
    """
    WebSocket endpoint for portfolio updates
    
    Args:
        websocket: WebSocket connection
        portfolio_id: Portfolio ID to monitor
        client_id: Client identifier
    """
    connection_manager = get_connection_manager()
    
    # Accept connection
    await connection_manager.connect(
        websocket,
        client_id,
        metadata={'portfolio_id': portfolio_id}
    )
    
    # Auto-subscribe to portfolio updates
    await connection_manager.subscribe(client_id, [f"portfolio:{portfolio_id}"])
    
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                if message.get('type') == 'ping':
                    await connection_manager.send_personal_message(
                        {'type': 'pong'},
                        client_id
                    )
            except json.JSONDecodeError:
                pass
    
    except WebSocketDisconnect:
        await connection_manager.disconnect(client_id)
        logger.info(f"Portfolio WebSocket disconnected for {portfolio_id}")
    
    except Exception as e:
        logger.error(f"Portfolio WebSocket error: {e}")
        await connection_manager.disconnect(client_id)


@router.websocket("/ws/market")
async def market_websocket(
    websocket: WebSocket,
    client_id: str = Query(..., description="Client identifier"),
    symbols: str = Query(..., description="Comma-separated symbols")
):
    """
    WebSocket endpoint for market data updates
    
    Args:
        websocket: WebSocket connection
        client_id: Client identifier
        symbols: Comma-separated market symbols
    """
    connection_manager = get_connection_manager()
    
    # Parse symbols
    symbol_list = [s.strip() for s in symbols.split(',')]
    
    # Accept connection
    await connection_manager.connect(
        websocket,
        client_id,
        metadata={'symbols': symbol_list}
    )
    
    # Auto-subscribe to market data for symbols
    topics = [f"market:{symbol}" for symbol in symbol_list]
    await connection_manager.subscribe(client_id, topics)
    
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                if message.get('type') == 'ping':
                    await connection_manager.send_personal_message(
                        {'type': 'pong'},
                        client_id
                    )
            except json.JSONDecodeError:
                pass
    
    except WebSocketDisconnect:
        await connection_manager.disconnect(client_id)
        logger.info(f"Market WebSocket disconnected")
    
    except Exception as e:
        logger.error(f"Market WebSocket error: {e}")
        await connection_manager.disconnect(client_id)


@router.get("/ws/stats")
async def websocket_stats():
    """
    Get WebSocket connection statistics
    
    Returns:
        Connection statistics
    """
    connection_manager = get_connection_manager()
    return connection_manager.get_connection_stats()

# Made with Bob

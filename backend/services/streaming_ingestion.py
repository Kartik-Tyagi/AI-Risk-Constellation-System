"""
Streaming Ingestion Service
Simulates real-time data streams with queue-based ingestion
"""

import logging
import queue
import threading
import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class StreamMessage:
    """Message in the stream"""
    message_type: str
    data: Dict[str, Any]
    timestamp: datetime
    source: str


class StreamingIngestionService:
    """Service for streaming data ingestion"""
    
    def __init__(
        self,
        batch_size: int = 100,
        batch_timeout: float = 5.0,
        max_queue_size: int = 10000
    ):
        """
        Initialize streaming ingestion service
        
        Args:
            batch_size: Number of messages per batch
            batch_timeout: Timeout for batch collection (seconds)
            max_queue_size: Maximum queue size
        """
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.queue: queue.Queue = queue.Queue(maxsize=max_queue_size)
        self.running = False
        self.worker_thread: Optional[threading.Thread] = None
        self.handlers: Dict[str, Callable] = {}
        self.stats = {
            'messages_received': 0,
            'messages_processed': 0,
            'batches_processed': 0,
            'errors': 0
        }
    
    def register_handler(self, message_type: str, handler: Callable) -> None:
        """
        Register a handler for a message type
        
        Args:
            message_type: Type of message
            handler: Handler function
        """
        self.handlers[message_type] = handler
        logger.info(f"Registered handler for message type: {message_type}")
    
    def ingest_message(self, message: StreamMessage) -> bool:
        """
        Ingest a single message
        
        Args:
            message: Stream message
            
        Returns:
            True if message was queued successfully
        """
        try:
            self.queue.put(message, block=False)
            self.stats['messages_received'] += 1
            return True
        except queue.Full:
            logger.warning("Queue is full, dropping message")
            self.stats['errors'] += 1
            return False
    
    def ingest_batch(self, messages: List[StreamMessage]) -> int:
        """
        Ingest a batch of messages
        
        Args:
            messages: List of stream messages
            
        Returns:
            Number of messages successfully queued
        """
        queued = 0
        for message in messages:
            if self.ingest_message(message):
                queued += 1
        return queued
    
    def _process_batch(self, batch: List[StreamMessage]) -> None:
        """Process a batch of messages"""
        # Group messages by type
        by_type: Dict[str, List[StreamMessage]] = {}
        for message in batch:
            if message.message_type not in by_type:
                by_type[message.message_type] = []
            by_type[message.message_type].append(message)
        
        # Process each type
        for message_type, messages in by_type.items():
            if message_type in self.handlers:
                try:
                    handler = self.handlers[message_type]
                    data_list = [msg.data for msg in messages]
                    handler(data_list)
                    self.stats['messages_processed'] += len(messages)
                except Exception as e:
                    logger.error(f"Error processing {message_type} messages: {e}")
                    self.stats['errors'] += len(messages)
            else:
                logger.warning(f"No handler registered for message type: {message_type}")
                self.stats['errors'] += len(messages)
        
        self.stats['batches_processed'] += 1
    
    def _worker_loop(self) -> None:
        """Worker thread loop"""
        batch: List[StreamMessage] = []
        last_batch_time = time.time()
        
        while self.running:
            try:
                # Try to get message with timeout
                try:
                    message = self.queue.get(timeout=0.1)
                    batch.append(message)
                except queue.Empty:
                    pass
                
                # Process batch if size reached or timeout
                current_time = time.time()
                should_process = (
                    len(batch) >= self.batch_size or
                    (len(batch) > 0 and (current_time - last_batch_time) >= self.batch_timeout)
                )
                
                if should_process:
                    self._process_batch(batch)
                    batch = []
                    last_batch_time = current_time
                    
            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
                time.sleep(1)
        
        # Process remaining messages
        if batch:
            self._process_batch(batch)
    
    def start(self) -> None:
        """Start the streaming ingestion service"""
        if self.running:
            logger.warning("Service is already running")
            return
        
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        logger.info("Streaming ingestion service started")
    
    def stop(self, timeout: float = 10.0) -> None:
        """
        Stop the streaming ingestion service
        
        Args:
            timeout: Timeout for graceful shutdown
        """
        if not self.running:
            return
        
        logger.info("Stopping streaming ingestion service...")
        self.running = False
        
        if self.worker_thread:
            self.worker_thread.join(timeout=timeout)
        
        logger.info("Streaming ingestion service stopped")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get ingestion statistics"""
        return {
            **self.stats,
            'queue_size': self.queue.qsize(),
            'is_running': self.running
        }
    
    def clear_queue(self) -> int:
        """Clear the queue and return number of messages cleared"""
        count = 0
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
                count += 1
            except queue.Empty:
                break
        return count


class MarketDataStream:
    """Simulates real-time market data stream"""
    
    def __init__(self, ingestion_service: StreamingIngestionService):
        self.service = ingestion_service
        self.running = False
        self.thread: Optional[threading.Thread] = None
    
    def start(self, assets: List[str], interval: float = 1.0) -> None:
        """
        Start streaming market data
        
        Args:
            assets: List of asset IDs
            interval: Update interval in seconds
        """
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(
            target=self._stream_loop,
            args=(assets, interval),
            daemon=True
        )
        self.thread.start()
        logger.info(f"Market data stream started for {len(assets)} assets")
    
    def _stream_loop(self, assets: List[str], interval: float) -> None:
        """Stream loop"""
        import random
        
        while self.running:
            for asset_id in assets:
                # Simulate market data
                base_price = 100.0
                price = base_price * (1 + random.uniform(-0.02, 0.02))
                
                message = StreamMessage(
                    message_type='market_data',
                    data={
                        'asset_id': asset_id,
                        'timestamp': datetime.now(),
                        'close_price': round(price, 2),
                        'volume': random.randint(100000, 1000000)
                    },
                    timestamp=datetime.now(),
                    source='market_data_stream'
                )
                
                self.service.ingest_message(message)
            
            time.sleep(interval)
    
    def stop(self) -> None:
        """Stop the stream"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5.0)
        logger.info("Market data stream stopped")


# Example usage
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Create service
    service = StreamingIngestionService(batch_size=10, batch_timeout=2.0)
    
    # Register handler
    def handle_market_data(data_list: List[Dict[str, Any]]) -> None:
        print(f"Processing batch of {len(data_list)} market data messages")
        for data in data_list:
            print(f"  {data['asset_id']}: ${data['close_price']}")
    
    service.register_handler('market_data', handle_market_data)
    
    # Start service
    service.start()
    
    # Start market data stream
    stream = MarketDataStream(service)
    stream.start(assets=['AAPL', 'MSFT', 'GOOGL'], interval=0.5)
    
    try:
        # Run for 10 seconds
        time.sleep(10)
    finally:
        stream.stop()
        service.stop()
        
        stats = service.get_stats()
        print(f"\nFinal stats: {stats}")

# Made with Bob

"""
Redis Streams Integration for ML Inference
===========================================

Async processing of thermal images through Redis Streams.

Streams:
- thermal:calibrated → Input for ML inference
- defect:detected → Output from ML inference
"""
import asyncio
import json
import logging
from typing import Dict, Optional, Any
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class MLStreamProcessor:
    """
    Process thermal images from Redis Streams.
    
    Consumes from: thermal:calibrated
    Produces to: defect:detected
    """
    
    def __init__(
        self,
        redis_host: str = "redis",
        redis_port: int = 6379,
        stream_in: str = "thermal:calibrated",
        stream_out: str = "defect:detected",
        group_name: str = "ml-inference",
        consumer_name: str = "ml-consumer-1"
    ):
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.stream_in = stream_in
        self.stream_out = stream_out
        self.group_name = group_name
        self.consumer_name = consumer_name
        self.redis: Optional[redis.Redis] = None
        self.running = False
    
    async def connect(self):
        """Connect to Redis and create consumer group."""
        self.redis = redis.Redis(
            host=self.redis_host,
            port=self.redis_port,
            decode_responses=True
        )
        
        # Create consumer group if not exists
        try:
            await self.redis.xgroup_create(
                self.stream_in,
                self.group_name,
                id="0",
                mkstream=True
            )
            logger.info(f"Created consumer group: {self.group_name}")
        except redis.exceptions.ResponseError as e:
            if "BUSYGROUP" in str(e):
                logger.debug(f"Consumer group {self.group_name} already exists")
            else:
                raise
        
        logger.info(f"Connected to Redis at {self.redis_host}:{self.redis_port}")
    
    async def disconnect(self):
        """Disconnect from Redis."""
        self.running = False
        if self.redis:
            await self.redis.close()
            logger.info("Disconnected from Redis")
    
    async def process_stream(self, pipeline, batch_size: int = 1):
        """
        Continuously process messages from stream.
        
        Args:
            pipeline: ML pipeline instance with infer method
            batch_size: Number of messages to process in batch
        """
        self.running = True
        logger.info(f"Starting stream processor (batch_size={batch_size})")
        
        while self.running:
            try:
                # Read messages from stream
                messages = await self.redis.xreadgroup(
                    groupname=self.group_name,
                    consumername=self.consumer_name,
                    streams={self.stream_in: ">"},
                    count=batch_size,
                    block=5000  # 5 second timeout
                )
                
                if not messages:
                    continue
                
                # Process messages
                for stream_name, stream_messages in messages:
                    for message_id, message_data in stream_messages:
                        try:
                            await self._process_message(pipeline, message_id, message_data)
                        except Exception as e:
                            logger.error(f"Error processing message {message_id}: {e}")
                            # Send to dead letter queue or mark as failed
                            await self._handle_failed_message(message_id, message_data, str(e))
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Stream processing error: {e}")
                await asyncio.sleep(1)
    
    async def _process_message(
        self,
        pipeline,
        message_id: str,
        message_data: Dict[str, str]
    ):
        """
        Process single message from stream.
        
        Args:
            pipeline: ML pipeline instance
            message_id: Redis stream message ID
            message_data: Message data dictionary
        """
        # Parse message data
        data = json.loads(message_data.get("data", "{}"))
        
        # Extract required fields
        image_id = data.get("image_id")
        module_id = data.get("module_id")
        inspection_id = data.get("inspection_id")
        thermal_data = data.get("thermal_data")  # Base64 encoded
        metadata = data.get("metadata", {})
        
        if not all([image_id, module_id, thermal_data]):
            logger.warning(f"Missing required fields in message {message_id}")
            await self.redis.xack(self.stream_in, self.group_name, message_id)
            return
        
        # Run ML inference
        import base64
        import numpy as np
        
        thermal_bytes = base64.b64decode(thermal_data)
        thermal_array = np.frombuffer(thermal_bytes, dtype=np.float32).reshape(640, 512)
        
        result = await pipeline.infer(
            image_id=image_id,
            module_id=module_id,
            inspection_id=inspection_id,
            thermal_data=thermal_array,
            metadata=metadata
        )
        
        # Publish result to defect:detected stream
        output_data = {
            "image_id": image_id,
            "module_id": module_id,
            "inspection_id": inspection_id,
            "defect_type": result.defect_type.value,
            "severity": result.severity.value,
            "severity_score": result.severity_score,
            "confidence": result.confidence,
            "temperature_delta": result.temperature_delta,
            "affected_cells": result.affected_cells,
            "recommendations": result.recommendations,
            "processing_time_ms": result.total_processing_time_ms,
            "timestamp": result.timestamp
        }
        
        await self.redis.xadd(
            self.stream_out,
            {"data": json.dumps(output_data)}
        )
        
        # Acknowledge message
        await self.redis.xack(self.stream_in, self.group_name, message_id)
        
        logger.info(
            f"Processed {image_id}: {result.defect_type.value} "
            f"({result.severity.value}, {result.confidence:.2%})"
        )
    
    async def _handle_failed_message(
        self,
        message_id: str,
        message_data: Dict[str, str],
        error: str
    ):
        """Handle failed message (dead letter queue)."""
        # Add to failed messages stream
        await self.redis.xadd(
            "ml:failed",
            {
                "original_message_id": message_id,
                "original_data": json.dumps(message_data),
                "error": error,
                "timestamp": asyncio.get_event_loop().time()
            }
        )
        
        # Acknowledge original message to remove from pending
        await self.redis.xack(self.stream_in, self.group_name, message_id)
        
        logger.warning(f"Message {message_id} moved to dead letter queue: {error}")
    
    async def get_pending_count(self) -> int:
        """Get count of pending messages."""
        if not self.redis:
            return 0
        
        info = await self.redis.xinfo_groups(self.stream_in)
        for group in info:
            if group.get("name") == self.group_name:
                return group.get("pending", 0)
        return 0
    
    async def get_stream_info(self) -> Dict[str, Any]:
        """Get stream information."""
        if not self.redis:
            return {}
        
        info = await self.redis.xinfo_stream(self.stream_in)
        return {
            "stream": self.stream_in,
            "length": info.get("length", 0),
            "groups": info.get("groups", 0),
            "last_generated_id": info.get("last-generated-id", "N/A")
        }


class StreamHealthChecker:
    """Monitor stream health and backpressure."""
    
    def __init__(self, redis: redis.Redis, stream_name: str):
        self.redis = redis
        self.stream_name = stream_name
    
    async def check_health(self) -> Dict[str, Any]:
        """Check stream health."""
        try:
            info = await self.redis.xinfo_stream(self.stream_name)
            
            length = info.get("length", 0)
            
            return {
                "status": "healthy" if length < 100 else "warning" if length < 500 else "critical",
                "stream_length": length,
                "first_entry": info.get("first-entry", "N/A"),
                "last_entry": info.get("last-entry", "N/A")
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }


# Example usage
async def main():
    """Example of using ML stream processor."""
    from pipeline import MLPipeline
    
    # Initialize components
    processor = MLStreamProcessor(
        redis_host="localhost",
        group_name="ml-inference-dev",
        consumer_name="consumer-1"
    )
    
    pipeline = MLPipeline(
        model_dir="./models",
        device="edge"
    )
    
    try:
        # Connect to Redis
        await processor.connect()
        
        # Start processing
        await processor.process_stream(pipeline, batch_size=1)
        
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await processor.disconnect()


if __name__ == "__main__":
    asyncio.run(main())

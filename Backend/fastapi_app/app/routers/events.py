# backend/fastapi_app/routers/events.py
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import asyncio
import json
import logging
from typing import Dict, Any

from ..services.redis_service import redis_client

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/subscribe/{user_id}")
async def subscribe_events(user_id: str):
    """Subscribe to real-time events for a user"""
    async def event_generator():
        """Generate SSE events"""
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(f"user:{user_id}")
        
        try:
            while True:
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=30
                )
                if message:
                    try:
                        data = json.loads(message['data'])
                        yield f"data: {json.dumps(data)}\n\n"
                    except json.JSONDecodeError:
                        yield f"data: {message['data']}\n\n"
                else:
                    # Send heartbeat to keep connection alive
                    yield ": heartbeat\n\n"
                    await asyncio.sleep(1)
        except asyncio.CancelledError:
            await pubsub.unsubscribe(f"user:{user_id}")
            await pubsub.close()
            logger.info(f"SSE connection closed for user {user_id}")
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.post("/publish")
async def publish_event(user_id: str, event_type: str, data: Dict[str, Any]):
    """Publish an event to a user"""
    from datetime import datetime
    
    event_data = {
        "type": event_type,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }
    
    await redis_client.publish(f"user:{user_id}", json.dumps(event_data))
    
    return {"status": "published", "user_id": user_id}
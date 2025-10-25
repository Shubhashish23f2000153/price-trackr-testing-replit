from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import init_db
from .api import api_router
from .utils.websocket import manager
import aioredis # Import aioredis
import asyncio
import json

app = FastAPI(
    title="PriceTrackr API",
    description="Global price tracking and comparison system",
    version="1.0.0"
)

# CORS Configuration (Using the "wide open" policy for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")


# --- NEW: Redis Pub/Sub Listener ---
async def redis_listener():
    """Listens to the 'price_updates' channel and broadcasts messages."""
    redis = await aioredis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    pubsub = redis.pubsub()
    await pubsub.subscribe("price_updates")
    print("Subscribed to 'price_updates' Redis channel.")
    
    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message["type"] == "message":
                print(f"Received from Redis: {message['data']}")
                try:
                    data = json.loads(message['data'])
                    await manager.broadcast(data) # Broadcast to all WS clients
                except json.JSONDecodeError:
                    print("Could not decode message data.")
            await asyncio.sleep(0.01) # Prevent blocking
    except asyncio.CancelledError:
        print("Redis listener cancelled.")
    finally:
        await pubsub.unsubscribe("price_updates")
        await redis.close()
        print("Unsubscribed and closed Redis.")

# --- MODIFIED: Startup Event ---
@app.on_event("startup")
async def startup_event():
    """Initialize database and start Redis listener"""
    init_db()
    print("✅ Database initialized")
    # Start the listener as a background task
    asyncio.create_task(redis_listener())


@app.get("/")
async def root():
    return {
        "message": "PriceTrackr API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.websocket("/ws/updates")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time price updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            await manager.send_personal_message(f"Echo: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
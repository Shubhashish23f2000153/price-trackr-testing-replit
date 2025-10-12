from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import init_db
from .api import api_router
from .utils.websocket import manager

app = FastAPI(
    title="PriceTrackr API",
    description="Global price tracking and comparison system",
    version="1.0.0"
)

# CORS Configuration
# Use this list of allowed origins
origins = [
    "http://localhost:5000",
    "http://localhost:3000",
    "chrome-extension://dldibmjmdmlnihpoadllbmnagdbeomi" # Your specific extension ID from the error message
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # <-- CHANGE THIS: Use the 'origins' list instead of ["*"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()
    print("✅ Database initialized")


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
            data = await websocket.receive_text()
            # Echo back for now - in production, this would handle subscriptions
            await manager.send_personal_message(f"Received: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

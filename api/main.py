"""
FastAPI backend for Polymr market making bot.
Provides REST API and WebSocket for bot control and real-time updates.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import bot, markets, orders
from websocket_manager import ws_manager
from database import init_db

app = FastAPI(
    title="Polymr API",
    description="Backend API for Polymr market making bot",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(bot.router, tags=["Bot"])
app.include_router(markets.router, tags=["Markets"])
app.include_router(orders.router, tags=["Orders"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "polymr-api"}


@app.on_event("startup")
async def startup_event():
    print("FastAPI application starting...")
    init_db()


@app.on_event("shutdown")
async def shutdown_event():
    print("FastAPI application shutting down...")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

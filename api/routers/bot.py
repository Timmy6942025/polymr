"""Bot control endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from bot import BotController, BotStateManager
from database import get_db
from schemas import BotStateCreate, BotStateResponse, BotStateUpdate

router = APIRouter(prefix="/bot", tags=["bot"])
bot_controller = BotController()
state_manager = BotStateManager()


@router.get("/state", response_model=BotStateResponse)
def get_bot_state():
    state = state_manager.get_state()
    if state is None:
        raise HTTPException(status_code=404, detail="Bot not initialized. Run setup first.")

    return state


@router.get("/status")
def get_bot_status():
    return {
        "is_running": bot_controller.is_running(),
        "is_stopped": state_manager.is_stopped(),
        "mode": state_manager.get_mode(),
    }


@router.get("/stats")
def get_bot_stats():
    state = state_manager.get_state()
    if state is None:
        raise HTTPException(status_code=404, detail="Bot not initialized")

    return {
        "total_orders": state.total_orders,
        "filled_orders": state.filled_orders,
        "total_volume": state.total_volume,
        "total_pnl": state.total_pnl,
        "fill_rate": state.filled_orders / state.total_orders if state.total_orders > 0 else 0.0,
    }


@router.post("/init", response_model=BotStateResponse)
def initialize_bot(config: BotStateCreate, db: Session = Depends(get_db)):
    existing = state_manager.get_state()
    if existing:
        raise HTTPException(status_code=400, detail="Bot already initialized")

    state = state_manager.initialize(config)
    return state


@router.post("/config")
def update_bot_config(update: BotStateUpdate):
    state = state_manager.update_config(update)
    if state is None:
        raise HTTPException(status_code=404, detail="Bot not initialized")

    return {"success": True, "state": state}


@router.post("/start")
def start_bot(capital: float, aggression: int, mode: str = "sandbox"):
    if not state_manager.get_state():
        raise HTTPException(status_code=400, detail="Bot not initialized. Run /bot/init first")

    result = bot_controller.start(capital=capital, aggression=aggression, mode=mode)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to start bot"))

    return result


@router.post("/stop")
def stop_bot():
    result = bot_controller.stop()

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to stop bot"))

    return result

"""
Configuration API router.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from .bot import BotConfigRequest, ConfigResponse

router = APIRouter()

# ============================================================================
# MODELS
# ============================================================================

class ConfigField(BaseModel):
    name: str
    value: Any
    type: str = "string"
    description: Optional[str] = None
    options: Optional[list[str]] = None

class ConfigSection(BaseModel):
    title: str
    fields: list[ConfigField]

class FullConfigResponse(BaseModel):
    sections: list[ConfigSection]

# ============================================================================
# ENDPOINTS
# ============================================================================

# NOTE: Configuration endpoints will be implemented in bot.py router
# to avoid duplication and keep single source of truth

# This router is reserved for future extension
@router.get("/schema", response_model=FullConfigResponse)
async def get_config_schema():
    """Get configuration schema for UI."""
    # Return configuration schema for the setup wizard
    return FullConfigResponse(sections=[])

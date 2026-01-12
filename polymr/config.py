"""
Configuration management for Polymarket Maker Rebates Bot.

Loads configuration from environment variables and config.yaml.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


# ============================================================================
# Configuration Models
# ============================================================================

class PolymarketConfig(BaseModel):
    """Polymarket API configuration."""
    api_url: str = "https://clob.polymarket.com"
    ws_url: str = "wss://clob-ws.polymarket.com"
    chain_id: int = 137  # Polygon


class AuthConfig(BaseModel):
    """Authentication configuration."""
    private_key: str = ""
    public_address: str = ""


class MarketDiscoveryConfig(BaseModel):
    """Market discovery configuration."""
    enabled: bool = True
    window_minutes: int = 15
    categories: List[str] = Field(default_factory=lambda: ["crypto", "bitcoin", "ethereum"])
    exclude_categories: List[str] = Field(default_factory=lambda: ["sports", "politics", "entertainment"])


class QuotingConfig(BaseModel):
    """Quoting strategy configuration."""
    # Order sizing
    default_size: float = 10.0
    min_size: float = 1.0
    max_size: float = 100.0

    # Spread configuration (basis points)
    min_spread_bps: int = 10
    max_spread_bps: int = 50
    spread_step_bps: int = 5

    # Price positioning from best bid/ask
    best_bid_offset_bps: int = 5
    best_ask_offset_bps: int = 5

    # Quote refresh timing
    quote_refresh_rate_ms: int = 1000
    order_lifetime_ms: int = 3000

    # Cancel/Replace cycle
    cancel_replace_interval_ms: int = 500
    taker_delay_ms: int = 500
    batch_cancellations: bool = True


class InventoryConfig(BaseModel):
    """Inventory management configuration."""
    # Exposure limits (USD)
    max_exposure_usd: float = 1000.0
    min_exposure_usd: float = -1000.0
    target_net_exposure: float = 0.0

    # Position limits
    max_position_size_usd: float = 500.0
    max_single_order_usd: float = 100.0

    # Skew protection
    max_inventory_skew: float = 0.3
    skew_rebalance_factor: float = 0.5


class RiskConfig(BaseModel):
    """Risk management configuration."""
    # Stop loss
    stop_loss_pct: float = 10.0
    stop_loss_cooldown_minutes: int = 30

    # Volume limits
    max_daily_volume_usd: float = 5000.0
    max_orders_per_minute: int = 60

    # Rebate optimization
    min_fill_probability: float = 0.5
    require_fee_market_only: bool = True

    # Validation
    pre_trade_validation: bool = True
    post_trade_validation: bool = True


class AutoRedeemConfig(BaseModel):
    """Auto-redeem configuration."""
    enabled: bool = True
    threshold_usd: float = 1.0
    auto_merge_enabled: bool = True
    check_interval_seconds: int = 60


class GasConfig(BaseModel):
    """Gas optimization configuration."""
    batching_enabled: bool = True
    gas_price_gwei: float = 30.0
    max_gas_percentage: float = 5.0
    priority: str = "standard"


class PolygonConfig(BaseModel):
    """Polygon RPC configuration."""
    rpc_url: str = "https://polygon-rpc.com"
    gas_oracle_url: str = "https://gasstation.polygon.technology/v2"


class MetricsConfig(BaseModel):
    """Metrics configuration."""
    enabled: bool = True
    host: str = "0.0.0.0"
    port: int = 9305


class TelegramConfig(BaseModel):
    """Telegram alerts configuration."""
    enabled: bool = False
    bot_token: str = ""
    chat_id: str = ""


class MonitoringConfig(BaseModel):
    """Monitoring configuration."""
    log_level: str = "INFO"
    metrics: MetricsConfig = Field(default_factory=MetricsConfig)
    structured_logging: bool = True
    telegram: TelegramConfig = Field(default_factory=TelegramConfig)


class BotConfig(BaseModel):
    """Bot settings configuration."""
    name: str = "polymr-maker-bot"
    test_mode: bool = True
    startup_delay_seconds: int = 5
    shutdown_grace_period: int = 10
    graceful_shutdown: bool = True


class Settings(BaseSettings):
    """Main settings class that combines all configuration sections."""

    # Main sections
    polymarket: PolymarketConfig = Field(default_factory=PolymarketConfig)
    auth: AuthConfig = Field(default_factory=AuthConfig)
    market_discovery: MarketDiscoveryConfig = Field(default_factory=MarketDiscoveryConfig)
    quoting: QuotingConfig = Field(default_factory=QuotingConfig)
    inventory: InventoryConfig = Field(default_factory=InventoryConfig)
    risk: RiskConfig = Field(default_factory=RiskConfig)
    auto_redeem: AutoRedeemConfig = Field(default_factory=AutoRedeemConfig)
    gas: GasConfig = Field(default_factory=GasConfig)
    polygon: PolygonConfig = Field(default_factory=PolygonConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    bot: BotConfig = Field(default_factory=BotConfig)

    class Config:
        env_prefix = "POLYMR_"
        env_nested_delimiter = "__"
        extra = "ignore"


# ============================================================================
# Configuration Loader
# ============================================================================

def load_config(config_path: Optional[str] = None) -> Settings:
    """
    Load configuration from YAML file and environment variables.

    Args:
        config_path: Path to config.yaml file. If None, looks in current directory.

    Returns:
        Settings object with all configuration loaded.
    """
    # Load dotenv first
    from dotenv import load_dotenv
    load_dotenv()

    settings = Settings()

    if config_path is None:
        # Look for config.yaml in current directory or parent directories
        search_paths = [
            Path.cwd() / "config.yaml",
            Path(__file__).parent.parent / "config.yaml",
            Path(__file__).parent.parent.parent / "config.yaml",
        ]
        for path in search_paths:
            if path.exists():
                config_path = str(path)
                break

    if config_path and Path(config_path).exists():
        with open(config_path, "r") as f:
            config_data = yaml.safe_load(f)

            if config_data:
                for section, values in config_data.items():
                    if hasattr(settings, section):
                        section_model = getattr(settings, section)
                        if isinstance(section_model, BaseModel):
                            for key, value in values.items():
                                if hasattr(section_model, key):
                                    setattr(section_model, key, value)

    # Override with environment variables
    settings.auth.private_key = os.getenv("PRIVATE_KEY", settings.auth.private_key)
    settings.auth.public_address = os.getenv("PUBLIC_ADDRESS", settings.auth.public_address)
    settings.polygon.rpc_url = os.getenv("RPC_URL", settings.polygon.rpc_url)

    return settings


def validate_config(settings: Settings) -> List[str]:
    """
    Validate configuration and return list of errors.

    Args:
        settings: Settings object to validate.

    Returns:
        List of error messages (empty if valid).
    """
    errors = []

    # Check authentication
    if not settings.auth.private_key:
        errors.append("PRIVATE_KEY is required")
    if not settings.auth.public_address:
        errors.append("PUBLIC_ADDRESS is required")

    # Validate private key format
    if settings.auth.private_key:
        if not settings.auth.private_key.startswith("0x"):
            errors.append("PRIVATE_KEY must start with 0x")
        elif len(settings.auth.private_key) != 66:
            errors.append("PRIVATE_KEY must be 66 characters (including 0x prefix)")

    # Validate quoting parameters
    if settings.quoting.min_spread_bps > settings.quoting.max_spread_bps:
        errors.append("MIN_SPREAD_BPS cannot be greater than MAX_SPREAD_BPS")

    # Validate inventory parameters
    if settings.inventory.max_exposure_usd < abs(settings.inventory.min_exposure_usd):
        errors.append("MAX_EXPOSURE_USD must be >= abs(MIN_EXPOSURE_USD)")

    # Validate risk parameters
    if settings.risk.stop_loss_pct < 0 or settings.risk.stop_loss_pct > 100:
        errors.append("STOP_LOSS_PCT must be between 0 and 100")

    return errors

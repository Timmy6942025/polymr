# Polymarket Maker Rebates Bot

A production-ready automated market-making bot for Polymarket's CLOB (Central Limit Order Book) designed to generate **passive income through maker rebates**.

## 🎯 Purpose

This bot automatically provides liquidity to Polymarket's 15-minute crypto markets by placing maker (limit) orders, earning **daily USDC rebates** on filled orders.

## 📊 Key Features

### Core Functionality
- **Real-time market making** on Polymarket CLOB
- **15-minute crypto market discovery** - automatically finds eligible markets
- **Passive order execution** - maker orders only to earn rebates
- **Inventory management** - balanced YES/NO exposure control
- **Risk management** - exposure limits, position caps, and validation

### Performance & Efficiency
- **Low-latency cancel/replace cycles** - optimized for 500ms taker delay
- **Gas batching** - minimizes Polygon transaction costs
- **WebSocket real-time updates** - instant orderbook tracking
- **Queue positioning** - optimized order placement for fills

### Monitoring & Control
- **Prometheus metrics** - real-time performance monitoring
- **Structured JSON logging** - full audit trail
- **Auto-redeem** - automatic settlement processing
- **Configurable via .env** - easy parameter tuning

## 💰 Revenue Model

### Maker Rebates Program
- **Target Markets**: 15-minute crypto markets only
- **Current Rebate Rate**: 100% (Jan 9-11, 2026), then 20%
- **Payout Frequency**: Daily in USDC
- **Max Fee Rate**: 1.56% at 50% probability

### How It Works
1. Place limit orders (maker) that provide liquidity
2. Orders get filled by other traders (takers)
3. Earn rebates on taker fees collected
4. Receive daily USDC payouts

## 🚀 Quick Start

### 1. Requirements
- Python 3.11+
- Ethereum private key with USDC on Polygon
- Polymarket account

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/polymr.git
cd polymr

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copy environment file
cp .env.example .env

# Edit with your credentials
nano .env
```

Required configuration:
```env
PRIVATE_KEY=your_private_key_here
PUBLIC_ADDRESS=your_wallet_address_here
RPC_URL=https://polygon-rpc.com

# Start with small values
DEFAULT_SIZE=10.0
MAX_EXPOSURE_USD=1000.0
TEST_MODE=true
```

### 4. Run the Bot

```bash
# Test mode (dry run, no real trades)
python -m polymr.main

# Production mode
# Set TEST_MODE=false in .env first
python -m polymr.main
```

## 📁 Project Structure

```
polymr/
├── polymr/
│   ├── __init__.py
│   ├── main.py                 # Entry point and orchestrator
│   ├── config.py               # Configuration management
│   ├── polymarket/
│   │   ├── __init__.py
│   │   ├── rest_client.py      # REST API client
│   │   ├── websocket_client.py # WebSocket client
│   │   ├── order_signer.py     # Order signing utilities
│   │   └── auth.py             # Authentication
│   ├── quoting/
│   │   ├── __init__.py
│   │   ├── quote_engine.py     # Quote generation
│   │   └── spread_calculator.py # Spread calculation
│   ├── inventory/
│   │   ├── __init__.py
│   │   └── inventory_manager.py # Position management
│   ├── execution/
│   │   ├── __init__.py
│   │   └── order_executor.py   # Order placement/cancellation
│   ├── risk/
│   │   ├── __init__.py
│   │   └── risk_manager.py     # Risk validation
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auto_redeem.py      # Settlement processing
│   │   └── market_discovery.py # Market discovery
│   └── monitoring/
│       ├── __init__.py
│       ├── metrics.py          # Prometheus metrics
│       └── logging.py          # Structured logging
├── config.yaml                 # Main configuration
├── .env.example               # Environment template
├── requirements.txt           # Dependencies
├── pyproject.toml            # Project metadata
└── README.md                 # This file
```

## ⚙️ Configuration Guide

### Quoting Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `DEFAULT_SIZE` | 10.0 | Base order size in USD |
| `MIN_SPREAD_BPS` | 10 | Minimum spread (0.10%) |
| `MAX_SPREAD_BPS` | 50 | Maximum spread (0.50%) |
| `QUOTE_REFRESH_RATE_MS` | 1000 | Quote update frequency |

### Risk Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `MAX_EXPOSURE_USD` | 1000.0 | Max net exposure in either direction |
| `STOP_LOSS_PCT` | 10.0 | Stop loss percentage |
| `MAX_SINGLE_ORDER_SIZE` | 100.0 | Max single order size |

### Optimization Tips

**For Higher Fill Rates:**
- Reduce `MIN_SPREAD_BPS` to 5-10 bps
- Increase `DEFAULT_SIZE` to 20-50
- Decrease `QUOTE_REFRESH_RATE_MS` to 500

**For Lower Risk:**
- Reduce `MAX_EXPOSURE_USD` to 500
- Increase `MIN_SPREAD_BPS` to 20-30
- Enable `STOP_LOSS_PCT` at 5%

**For Gas Savings:**
- Enable `GAS_BATCHING_ENABLED=true`
- Increase `QUOTE_REFRESH_RATE_MS` to 2000
- Set `BATCH_CANCELLATIONS=true`

## 📈 Expected Performance

Based on market conditions and configuration:

| Metric | Expected Range |
|--------|----------------|
| Fill Rate | 60-80% passive fills |
| Inventory Skew | <30% maintained |
| Quote Latency | <100ms |
| Daily Rebate Yield | 0.5-2% of volume |

## 🔒 Safety & Risk

### Important Warnings
⚠️ **Market making involves capital risk**
- Test thoroughly with small amounts first
- Monitor exposure and inventory continuously
- Gas costs can be significant during high network activity

### Best Practices
1. Start with `TEST_MODE=true` to verify configuration
2. Begin with small `DEFAULT_SIZE` and `MAX_EXPOSURE_USD`
3. Monitor logs for risk check failures
4. Review trading activity regularly
5. Comply with Polymarket terms of service

## 📊 Monitoring

### Prometheus Metrics
Access at `http://localhost:9305/metrics`:
- `polymr_orders_placed_total` - Total orders by side/outcome
- `polymr_orders_filled_total` - Total passive fills
- `polymr_inventory` - Current YES/NO positions
- `polymr_exposure_usd` - Net exposure in USD
- `polymr_rebates_earned_usd` - Cumulative rebates
- `polymr_quote_latency_ms` - Quote generation latency

### Structured Logging
All events logged as JSON with:
- Timestamp and log level
- Event type and details
- Correlation IDs for tracing

## 🐳 Docker Deployment

```bash
# Build and run
docker compose up --build -d

# View logs
docker compose logs -f polymr-bot

# Stop
docker compose down
```

## 📝 License

MIT License - See LICENSE file for details.

## 🤝 Contributing

Contributions welcome! Please read contributing guidelines first.

## 📞 Support

- GitHub Issues: For bug reports and feature requests
- Documentation: See docs/ directory
- Telegram: Community support channel

## 🙏 Acknowledgments

- Polymarket team for the CLOB infrastructure
- Open-source market making implementations
- The prediction market community

---

**Disclaimer**: This software is experimental. Use at your own risk. Past performance does not guarantee future results. Always test thoroughly before deploying with real funds.

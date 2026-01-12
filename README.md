# Polymr - DeFi & Prediction Market Income Platform

A unified platform for **passive income** through DeFi yield farming and **Polymarket maker rebates**.

## 🎯 Two Income Streams

### 1. DeFi Yield Farming (Frontend)
- Stake ETH → Earn 3.5% APY (Lido)
- Lend USDC → Earn 5-9% APY (Aave, Compound, Ledn)
- Solana staking → Earn 7% APY (Marinade)
- Real-world assets → Earn 10.5% APY (Centrifuge)

### 2. Polymarket Maker Rebates (Backend)
- Provide liquidity to 15-minute crypto markets
- Earn **100% rebate** on taker fees (limited time)
- Daily USDC payouts
- Fully automated trading bot

---

## 🚀 Quick Start

### Frontend (DeFi Dashboard)

```bash
cd /home/timmy/polymr

# Install dependencies
npm install

# Start development server
npm run dev

# Open http://localhost:5173
```

**Features:**
- MetaMask wallet connection
- Browse 6 DeFi protocols with real-time APY
- Portfolio tracking with local storage
- Yield calculator for estimated earnings
- Risk filtering (Low Risk, Stake, Lend)

### Backend (Polymarket Bot)

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your PRIVATE_KEY and PUBLIC_ADDRESS

# Run in test mode
python -m polymr.main

# For production, set TEST_MODE=false in .env
```

---

## 💰 How to Profit

### DeFi Yield Farming

| Protocol | Type | APY | Risk |
|----------|------|-----|------|
| Lido | ETH Staking | 3.5% | 🛡️ Low |
| Marinade | SOL Staking | 7.0% | 🛡️ Low |
| Aave | USDC Lending | 5.2% | 🛡️ Low |
| Compound | USDC Lending | 4.8% | 🛡️ Low |
| Centrifuge | RWA | 10.5% | ⚠️ Medium |
| Ledn | USDC Lending | 9.2% | ⚠️ Medium |

**Steps:**
1. Connect MetaMask wallet
2. Select a protocol
3. Deposit tokens
4. Track earnings in Portfolio

### Polymarket Maker Rebates

**Revenue Model:**
- Place maker (limit) orders on 15-minute crypto markets
- When takers fill your orders, you earn rebates on their fees
- **Current rebate rate: 100%** (limited time offer)
- Daily USDC payouts to your wallet

**Bot Configuration:**
```env
# In .env file
PRIVATE_KEY=your_private_key        # From MetaMask
PUBLIC_ADDRESS=your_address         # Your wallet address
RPC_URL=https://polygon-rpc.com     # Polygon RPC

# Start small
DEFAULT_SIZE=10.0
MAX_EXPOSURE_USD=1000.0

# Enable for production
TEST_MODE=false
```

---

## 📁 Project Structure

```
polymr/
├── src/                          # React Frontend
│   ├── main.tsx                  # Entry point
│   ├── App.tsx                   # Main app with wallet connection
│   ├── types.ts                  # TypeScript interfaces
│   ├── store.ts                  # Zustand state + PROTOCOLS data
│   ├── index.css                 # Tailwind styles
│   ├── hooks/
│   │   ├── useWallet.ts          # MetaMask connection
│   │   └── useProtocols.ts       # Protocol filtering
│   └── components/
│       ├── ProtocolCard.tsx      # Protocol display
│       ├── WalletButton.tsx      # Connect/disconnect
│       ├── DepositModal.tsx      # Yield calculator
│       └── Portfolio.tsx         # Positions dashboard
│
├── polymr/                       # Python Backend
│   ├── main.py                   # Bot orchestrator
│   ├── config.py                 # Configuration management
│   ├── polymarket/               # API clients
│   │   ├── rest_client.py        # REST API
│   │   └── websocket_client.py   # WebSocket
│   ├── quoting/                  # Quote engine
│   ├── execution/                # Order executor
│   ├── risk/                     # Risk management
│   └── monitoring/               # Metrics
│
├── config.yaml                   # Bot configuration
├── .env.example                  # Environment template
├── requirements.txt              # Python dependencies
├── package.json                  # Node dependencies
└── README.md                     # This file
```

---

## ⚙️ Configuration

### Frontend
No configuration required. Runs out of the box.

### Backend (config.yaml)

```yaml
quoting:
  default_size: 10.0          # Order size in USD
  min_spread_bps: 10          # 0.10% minimum spread
  max_spread_bps: 50          # 0.50% maximum spread

inventory:
  max_exposure_usd: 1000.0    # Maximum position size
  max_inventory_skew: 0.3     # 30% max imbalance

risk:
  stop_loss_pct: 10.0         # Stop loss percentage
  pre_trade_validation: true  # Validate before trading

bot:
  test_mode: true             # Set to false for production
```

---

## 🔒 Security

- Never share your PRIVATE_KEY
- Start with TEST_MODE=true
- Use a dedicated wallet with limited funds
- Monitor your positions regularly
- Comply with Polymarket terms of service

---

## 📊 Monitoring

### Prometheus Metrics
Access at `http://localhost:9305/metrics`:
- `polymr_orders_placed_total` - Total orders placed
- `polymr_orders_filled_total` - Total fills (rebates earned)
- `polymr_rebates_earned_usd` - Cumulative rebates in USDC

### Logs
Structured JSON logging with full audit trail.

---

## 🛠️ Development

### Run Frontend
```bash
npm run dev          # Development server
npm run build        # Production build
npm run preview      # Preview production build
```

### Run Backend
```bash
python -m polymr.main                    # Run bot
python -m polymr.main --config config.yaml  # Custom config
```

---

## ⚠️ Disclaimer

This software is experimental. Use at your own risk. Past performance does not guarantee future results. Always:
- Test thoroughly with small amounts
- Understand the risks of DeFi and market making
- Never invest more than you can afford to lose

---

**Start earning passive income today! 🚀**

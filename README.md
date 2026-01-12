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
- Earn **20% rebate** on taker fees (Jan 12-18, 2026 promo)
- Daily USDC payouts
- Fully automated trading bot with real-time fills

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

# Install py_clob_client for real trading
pip install py_clob_client

# Sandbox mode (simulated fills, real market data)
python run_bot.py 60 2 --sandbox

# Real mode (requires credentials)
export POLYMARKET_PRIVATE_KEY=your_key
export POLYMARKET_FUNDER=your_address
python run_bot.py 60 2 --real
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
- **Current rebate rate: 20%** (Jan 12-18, 2026 promo period)
- Daily USDC payouts to your wallet

**Bot Configuration (run_bot.py):**
```bash
# Aggression levels:
# 1 = Conservative (10% capital per order, 15-50 bps spread)
# 2 = Moderate (20% capital per order, 8-30 bps spread)  
# 3 = Aggressive (30% capital per order, 3-20 bps spread)

# Sandbox mode (recommended for testing)
python run_bot.py 60 2 --sandbox

# Real trading (requires environment variables)
export POLYMARKET_PRIVATE_KEY=your_wallet_private_key
export POLYMARKET_FUNDER=your_funder_address
python run_bot.py 60 2 --real
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
├── run_bot.py                    # Main trading bot (Real + Sandbox modes)
├── launch.py                     # Interactive launcher
├── requirements.txt              # Python dependencies
├── package.json                  # Node dependencies
└── README.md                     # This file
```

---

## 🤖 Trading Bot Architecture

### TradingClient Interface

```python
TradingClient (ABC)
├── RealTradingClient          # Real trading via py_clob_client
│   ├── EIP-712 order signing
│   ├── WebSocket for fills (wss://ws-subscriptions-clob.polymarket.com)
│   ├── Dynamic gas from Polygon RPC
│   └── API credential management
│
└── SandboxTradingClient       # Real data, simulated fills
    ├── Real markets from gamma-api.polymarket.com
    ├── Real orderbook from clob.polymarket.com/orderbook
    ├── Real fees from clob.polymarket.com/fee-rate
    ├── Real trades from clob.polymarket.com/trades
    └── Probabilistic fill simulation
```

### Key Features
- **Order Lifecycle**: submit → open → filled/cancelled/expired
- **Nonce Management**: Atomic increment for order signing
- **Gas Estimation**: Dynamic from `eth_gasPrice` RPC
- **Fill Detection**: WebSocket + /trades polling fallback
- **Risk Management**: Max position, net exposure, skew limits

---

## 🔒 Security

- Never share your `POLYMARKET_PRIVATE_KEY`
- Start with `--sandbox` mode
- Use a dedicated wallet with limited funds
- Monitor your positions regularly
- Comply with Polymarket terms of service

---

## 📊 Monitoring

The bot outputs real-time stats:

```
Cycle 5 | Placed: 20 | Filled: 3
  BTC > $98K in next 15m?
  0.5627 | 156 bps | $31,679
  📦 YES:5.2 NO:0.0 | Skew: 25%
  BUY 24.00 @ 0.5610 | Gas: $0.04
  📊 3/20 fills (15%) | Gas: $0.80 | Net: $1.20
```

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
# Sandbox (simulated trading)
python run_bot.py 60 2 --sandbox

# Real trading
export POLYMARKET_PRIVATE_KEY=...
export POLYMARKET_FUNDER=...
python run_bot.py 60 2 --real
```

### Dependencies
```
py_clob_client>=0.34.0    # Official Polymarket CLOB client
httpx                      # HTTP client for REST APIs
websocket-client           # WebSocket for real-time fills
```

---

## ⚠️ Disclaimer

This software is experimental. Use at your own risk. Past performance does not guarantee future results. Always:
- Test thoroughly with `--sandbox` mode first
- Understand the risks of DeFi and market making
- Never invest more than you can afford to lose

---

**Start earning passive income today! 🚀**

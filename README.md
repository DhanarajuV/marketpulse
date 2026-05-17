# 🎯 MarketPulse — Autonomous Market Intelligence System

An AI-powered market scanner that runs twice daily, analyzes 50+ stocks across 8 sectors, detects high-conviction trading opportunities, and sends Telegram alerts with entry/exit levels and position sizing.

## How It Works

```
8AM & 1PM EST (Mon-Fri)
    │
    ▼
Fetch prices for 52 tickers (yFinance)
    │
    ▼
Calculate indicators (RSI, MACD, MA, volume)
    │
    ▼
Run 5 signal detectors in parallel:
  • Panic Sell (oversold + no bad news)
  • Short Squeeze (high short interest + momentum)
  • Technical Breakout (MA cross, resistance break)
  • Chart Patterns (double bottom, cup & handle)
  • News Catalyst (sector-moving events)
    │
    ▼
Filter by fundamentals (P/E, revenue, debt)
    │
    ▼
Adjust conviction by market regime (VIX)
    │
    ▼
Synthesize (deduplicate, boost multi-signal tickers)
    │
    ▼
Send Telegram alerts with entry, targets, stop-loss
```

## Signal Types

| Signal | What It Detects | Conviction Boost |
|--------|----------------|-----------------|
| 🚨 Panic Sell | Quality stock drops 5%+ on no news, RSI < 30 | VIX > 30 (extreme fear) |
| 🔥 Short Squeeze | Short interest > 20%, price rising on volume | Multiple confirmations |
| 📈 Breakout | Price breaks resistance on 1.5x+ volume | Golden cross + volume |
| 📊 Chart Pattern | Double bottom, cup & handle | Pattern + volume |
| 📰 News Catalyst | Sector-wide positive catalyst | Multiple tickers affected |

## Alert Format

Every signal includes:
- Entry price
- 3 exit targets (scale-out strategy)
- Stop-loss level
- Time stop (max holding period)
- Position sizing (2% max risk per trade)
- Conviction level (LOW / MEDIUM / HIGH)

## Sector Coverage (52 tickers)

| Sector | ETF | Stocks |
|--------|-----|--------|
| Tech | QQQ | AAPL, MSFT, GOOGL, META, NVDA, CRM |
| Semiconductors | SMH | NVDA, AMD, AVGO, TSM, INTC, MU, QCOM |
| Energy | XLE | XOM, CVX, SLB, OXY, COP |
| Defense | ITA | LMT, RTX, NOC, GD, BA, PLTR |
| Healthcare | XLV | UNH, JNJ, LLY, PFE, ABBV, TMO |
| Financials | XLF | JPM, BAC, GS, V, MA |
| Consumer | XLY | AMZN, TSLA, HD, NKE, COST |
| Industrials | XLI | CAT, HON, UPS, DE, GE |

## Setup

### Prerequisites
- Python 3.13+
- API keys: [Gemini](https://aistudio.google.com/apikey) (free), [Tavily](https://app.tavily.com) (free), [Telegram Bot](https://t.me/BotFather)

### Installation

```bash
git clone https://github.com/DhanarajuV/marketpulse.git
cd marketpulse
python3.13 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo "$(pwd)" > venv/lib/python3.13/site-packages/marketpulse.pth
cp .env.example .env  # Fill in your API keys
```

### Run

```bash
# Manual scan
python src/scanner/run_scan.py

# Check specific ticker
python cli.py check --ticker NVDA

# Check a sector
python cli.py sector --sector semiconductors

# View signal history
python cli.py history

# Start scheduler (auto-runs 8AM & 1PM EST)
python src/scheduler.py

# Start API server
python src/api/main.py
```

## Deployment Options

### GitHub Actions (recommended, $0)
Push to GitHub, add secrets. Scans run automatically at 8AM/1PM EST.

### Local (development)
```bash
python src/scheduler.py  # Leave running
```

### Oracle Cloud VM ($0, always-on)
Free tier VM with cron jobs + FastAPI always running.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /auth/login | Login with email, get JWT |
| GET | /auth/me | Current user info |
| GET | /signals/active | Active open positions |
| GET | /signals/history | Past signals + outcomes |
| GET | /signals/stats | Win rate, returns |
| POST | /signals/scan | Trigger manual scan |
| POST | /signals/check | Check specific ticker |
| GET | /admin/users | List authorized users |
| POST | /admin/users | Add user |
| DELETE | /admin/users/{email} | Remove user |

API docs: `http://localhost:8000/docs`

## Tech Stack

| Component | Technology | Cost |
|-----------|-----------|------|
| Price Data | yFinance | Free |
| Technical Analysis | ta + pandas + numpy + scipy | Free |
| News | Tavily (1000/month) | Free |
| LLM (synthesis) | Gemini 2.5 Flash | Free |
| Alerts | Telegram Bot API | Free |
| Storage | SQLite | Free |
| API | FastAPI | Free |
| Scheduling | APScheduler / GitHub Actions | Free |

**Total cost: $0/month**

## Project Structure

```
marketpulse/
├── src/
│   ├── scanner/
│   │   ├── price_scanner.py       # Batch fetch + indicators
│   │   └── run_scan.py            # Full scan orchestration
│   ├── agents/
│   │   ├── panic_detector.py      # Mean reversion signals
│   │   ├── squeeze_detector.py    # Short squeeze detection
│   │   ├── technical_agent.py     # MA cross, resistance break
│   │   ├── chart_patterns.py      # Double bottom, cup & handle
│   │   ├── news_catalyst.py       # Tavily + Gemini news analysis
│   │   ├── market_regime.py       # VIX-based conviction adjustment
│   │   ├── fundamentals.py        # P/E, revenue, debt filter
│   │   ├── synthesis.py           # Deduplicate + boost multi-signal
│   │   └── position_monitor.py    # Track targets, stops, time limits
│   ├── api/
│   │   └── main.py                # FastAPI backend with auth
│   ├── core/
│   │   ├── config.py              # YAML config loader
│   │   └── universe.py            # Sector/ticker definitions
│   ├── alerts/
│   │   └── telegram.py            # Telegram bot alerts
│   ├── storage/
│   │   └── database.py            # SQLite operations
│   └── scheduler.py               # APScheduler (8AM/1PM)
├── cli.py                         # CLI interface
├── config/
│   └── settings.yaml              # All configuration
├── .github/workflows/
│   └── scan.yml                   # GitHub Actions scheduler
├── data/
│   └── marketpulse.db             # Signal database (gitignored)
├── .env.example
├── requirements.txt
└── README.md
```

## Design Principles

1. **Silence is golden** — no signal = no alert
2. **Every signal has an exit plan** — entry, targets, stop-loss, time limit
3. **Multiple confirmation** — single indicator is noise, 2+ is signal
4. **Sector context** — stock vs sector comparison, not absolute moves
5. **Fundamentals filter** — only signal quality companies (except squeezes)
6. **Risk management** — 2% max risk per trade, position sizing included

# MarketPulse — Complete Specification

## 1. Product Overview

### 1.1 What It Is
An autonomous market intelligence system that scans 50+ stocks across 8 sectors twice daily, identifies high-conviction trading opportunities, and alerts the admin via Telegram. Authorized users can log in to view signals and run on-demand scans.

### 1.2 Core Principles
- **Silence is golden** — no signal = no alert
- **Every signal has an exit plan** — entry, targets, stop-loss, time limit
- **Multiple confirmation required** — single indicator is noise, 2+ is signal
- **Backtest everything** — track accuracy to build trust before real money
- **Sector context** — compare stock to its sector, not just absolute moves

### 1.3 Users
- **Admin** (single user, your email): Receives Telegram alerts, manages authorized users
- **Authorized Users** (whitelist): Login via Google, view dashboard, run on-demand scans

---

## 2. Signal Types

### 2.1 Panic Sell Detection (Mean Reversion)
**Trigger conditions (ALL must be true):**
- Stock drops ≥5% in 1-2 days
- RSI < 30 (oversold)
- Sector ETF is NOT down proportionally (stock-specific, not market-wide)
- No fundamental bad news found in last 24h

**Thesis**: Market overreaction on quality stock → recovery in 1-2 weeks

**Exit calculation:**
- Stop-loss: 20% below entry OR recent support (whichever is tighter)
- Target 1: Price before the drop (recovery to pre-panic level)
- Target 2: 50-day MA
- Target 3: Recent 52-week high area
- Time stop: 14 days

### 2.2 News Catalyst
**Trigger conditions (ANY):**
- Sector-wide policy/regulation change (CHIPS Act, defense budget, etc.)
- Earnings beat + stock still near lows (market hasn't reacted)
- Supply chain shift benefiting specific companies
- Macro event creating sector tailwind

**Thesis**: News creates tailwind not yet fully priced in

**Exit calculation:**
- Stop-loss: Below pre-news price level
- Target 1: +10% (initial reaction)
- Target 2: +20% (full pricing-in)
- Target 3: Sector leader's valuation multiple
- Time stop: 21 days

### 2.3 Technical Breakout
**Trigger conditions (ALL must be true):**
- Price breaks above resistance level on volume ≥1.5x average
- OR golden cross (50-day MA crosses above 200-day MA)
- RSI between 50-70 (momentum but not overbought)

**Thesis**: Breakout + volume = trend continuation

**Exit calculation:**
- Stop-loss: Just below the breakout level (now support)
- Target 1: Measured move (height of pattern added to breakout)
- Target 2: Next resistance level
- Target 3: 1.5x measured move
- Time stop: 30 days

### 2.4 Short Squeeze
**Trigger conditions (ALL must be true):**
- Short interest > 20% of float
- Days to cover > 5
- Price rising (up ≥3% in last 5 days)
- Volume ≥2x average (shorts starting to cover)

**Thesis**: Forced covering creates snowball buying

**Exit calculation:**
- Stop-loss: 20% below entry
- Target 1: +15%
- Target 2: +25%
- Target 3: Entry × (1 + short_interest × 2), capped at +50%
- Time stop: 14 days

### 2.5 Market Regime (Context Only)
**Indicators monitored:**
- VIX level and direction
- Put/call ratio
- Advance/decline ratio
- Sector rotation patterns

**Not a trade signal itself** — modifies conviction of other signals:
- VIX > 30 (extreme fear) → panic sell signals get HIGHER conviction
- VIX < 15 (complacency) → breakout signals get LOWER conviction

---

## 3. Sector Universe

### 3.1 Tickers (52 total)

```yaml
sectors:
  tech:
    etf: QQQ
    stocks: [AAPL, MSFT, GOOGL, META, NVDA, CRM]
  semiconductors:
    etf: SMH
    stocks: [NVDA, AMD, AVGO, TSM, INTC, MU, QCOM]
  energy:
    etf: XLE
    stocks: [XOM, CVX, SLB, OXY, COP]
  defense:
    etf: ITA
    stocks: [LMT, RTX, NOC, GD, BA, PLTR]
  healthcare:
    etf: XLV
    stocks: [UNH, JNJ, LLY, PFE, ABBV, TMO]
  financials:
    etf: XLF
    stocks: [JPM, BAC, GS, V, MA, BRK-B]
  consumer:
    etf: XLY
    stocks: [AMZN, TSLA, HD, NKE, COST]
  industrials:
    etf: XLI
    stocks: [CAT, HON, UPS, DE, GE]
```

### 3.2 Market-Wide Indicators
- SPY (S&P 500)
- VIX (volatility/fear index)
- TLT (bonds — inverse correlation with stocks)
- DXY or UUP (dollar strength)

---

## 4. Architecture

### 4.1 System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    Oracle Cloud VM (free tier)                   │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Cron (8AM & 1PM EST)                                     │  │
│  │  └── python src/scanner/run_scan.py                       │  │
│  └───────────────────────────┬───────────────────────────────┘  │
│                              ▼                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  FastAPI Server (always running, port 8000)               │  │
│  │                                                           │  │
│  │  Auth:                                                    │  │
│  │    POST /auth/google     → verify Google token            │  │
│  │    GET  /auth/me         → current user info              │  │
│  │                                                           │  │
│  │  Admin:                                                   │  │
│  │    POST /admin/users     → add authorized user            │  │
│  │    DELETE /admin/users    → remove user                   │  │
│  │    GET  /admin/users     → list users                     │  │
│  │                                                           │  │
│  │  Signals:                                                 │  │
│  │    GET  /signals/active  → current open positions         │  │
│  │    GET  /signals/history → past signals + outcomes        │  │
│  │    POST /signals/scan    → trigger manual full scan       │  │
│  │    POST /signals/check   → check specific ticker/sector  │  │
│  │                                                           │  │
│  └───────────────────────────┬───────────────────────────────┘  │
│                              │                                  │
│  ┌───────────────────────────┼───────────────────────────────┐  │
│  │  SQLite (data/marketpulse.db)                             │  │
│  │    • users table                                          │  │
│  │    • signals table                                        │  │
│  │    • scan_logs table                                      │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Next.js Frontend (port 3000)                             │  │
│  │    • Google login                                         │  │
│  │    • Dashboard (active signals, charts)                   │  │
│  │    • History (past signals, win rate)                     │  │
│  │    • On-demand scan trigger                               │  │
│  │    • Admin panel (user management)                        │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
         │
         │ Telegram API
         ▼
┌─────────────────┐
│  Admin's Phone  │
│  (alerts)       │
└─────────────────┘
```

### 4.2 Scan Pipeline (runs at 8AM & 1PM)

```
Step 1: DATA COLLECTION (parallel, ~30 seconds)
  ├── Batch fetch prices for all 52 tickers (yFinance, 6 months)
  ├── Fetch sector ETF prices for comparison
  ├── Fetch market indicators (VIX, SPY)
  ├── Fetch short interest data
  └── Fetch sector news (Tavily, 1 query per sector = 8 queries)

Step 2: INDICATOR CALCULATION (~5 seconds)
  For each ticker:
  ├── RSI (14-day)
  ├── MACD
  ├── 50-day MA, 200-day MA
  ├── 20-day average volume
  ├── Daily/weekly % change
  ├── Distance from 52-week high/low
  └── Relative performance vs sector ETF

Step 3: SIGNAL DETECTION (parallel, ~10 seconds)
  ├── Panic Sell Detector → list of candidates
  ├── News Catalyst Analyzer → list of catalysts
  ├── Technical Breakout Scanner → list of breakouts
  └── Short Squeeze Detector → list of squeeze candidates

Step 4: ACTIVE POSITION CHECK (~5 seconds)
  For each active signal in DB:
  ├── Check if Target 1/2/3 hit → generate SELL alert
  ├── Check if stop-loss hit → generate EXIT alert
  └── Check if time stop reached → generate TIMEOUT alert

Step 5: SYNTHESIS (~10 seconds, LLM call)
  ├── Filter: only keep signals with 2+ confirming factors
  ├── Calculate exit levels for each signal
  ├── Calculate position sizing
  ├── Assign conviction (LOW/MEDIUM/HIGH)
  └── Generate human-readable alert text

Step 6: OUTPUT
  ├── Save new signals to DB (status: active)
  ├── Update closed signals in DB (status: closed, outcome: win/loss)
  ├── Send Telegram alerts to admin
  └── Log scan metadata (timestamp, signals found, errors)

Total scan time: ~60 seconds
```

---

## 5. Data Models

### 5.1 Database Schema (SQLite)

```sql
-- Users who can access the system
CREATE TABLE users (
    email TEXT PRIMARY KEY,
    name TEXT,
    role TEXT CHECK(role IN ('admin', 'user')) DEFAULT 'user',
    receive_alerts INTEGER DEFAULT 0,  -- 1 = gets Telegram alerts
    telegram_chat_id TEXT,             -- for per-user alerts (optional)
    added_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trading signals (both active and historical)
CREATE TABLE signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    signal_type TEXT NOT NULL,  -- panic_sell, news_catalyst, breakout, short_squeeze
    conviction TEXT NOT NULL,   -- LOW, MEDIUM, HIGH
    
    -- Entry
    entry_price REAL NOT NULL,
    entry_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Exit targets
    stop_loss REAL NOT NULL,
    target_1 REAL NOT NULL,
    target_2 REAL,
    target_3 REAL,
    time_stop_date TIMESTAMP NOT NULL,
    
    -- Position sizing
    suggested_shares INTEGER,
    suggested_position_value REAL,
    max_risk_dollars REAL,
    
    -- Status tracking
    status TEXT DEFAULT 'active',  -- active, closed_win, closed_loss, closed_timeout
    close_price REAL,
    close_date TIMESTAMP,
    return_pct REAL,
    
    -- Reasoning
    reasoning TEXT,          -- JSON: list of factors that triggered signal
    sector TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Scan execution logs
CREATE TABLE scan_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    scan_type TEXT,          -- scheduled, manual
    triggered_by TEXT,       -- 'cron' or user email
    tickers_scanned INTEGER,
    signals_found INTEGER,
    errors TEXT,             -- JSON: any API failures
    duration_seconds REAL
);
```

### 5.2 Signal Data Model (Python)

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Signal:
    ticker: str
    signal_type: str          # panic_sell, news_catalyst, breakout, short_squeeze
    conviction: str           # LOW, MEDIUM, HIGH
    entry_price: float
    stop_loss: float
    target_1: float
    target_2: Optional[float]
    target_3: Optional[float]
    time_stop_days: int
    reasoning: list[str]      # ["RSI at 24", "Down 7% vs sector -1%", "No bad news"]
    sector: str
    suggested_shares: Optional[int] = None
    position_value: Optional[float] = None
    max_risk: Optional[float] = None

@dataclass
class SellAlert:
    ticker: str
    reason: str               # "Target 1 hit", "Stop-loss triggered", "Time stop"
    current_price: float
    entry_price: float
    return_pct: float
    action: str               # "Sell 1/3", "Exit all", "Move stop to breakeven"
```

---

## 6. API Specification

### 6.1 Authentication

```
POST /auth/google
  Body: { "token": "google_id_token" }
  Response: { "access_token": "jwt_token", "user": { "email", "role" } }
  Logic: Verify Google token → check email in users table → issue JWT

GET /auth/me
  Headers: Authorization: Bearer <jwt>
  Response: { "email", "role", "name" }
```

### 6.2 Admin Endpoints (admin role only)

```
GET /admin/users
  Response: [{ "email", "role", "created_at" }]

POST /admin/users
  Body: { "email": "user@gmail.com", "name": "John" }
  Response: { "email", "role": "user", "created_at" }

DELETE /admin/users/{email}
  Response: 204
```

### 6.3 Signal Endpoints (any authenticated user)

```
GET /signals/active
  Response: [Signal objects with status='active']

GET /signals/history?days=30
  Response: [Signal objects with status='closed_*']

GET /signals/stats
  Response: {
    "total_signals": 45,
    "win_rate": 0.72,
    "avg_return": 8.3,
    "by_type": { "panic_sell": { "count": 20, "win_rate": 0.80 }, ... }
  }

POST /signals/scan
  Body: { "type": "full" } or { "type": "sector", "sector": "semiconductors" }
  Response: { "signals_found": 2, "signals": [Signal] }

POST /signals/check
  Body: { "ticker": "NVDA" }
  Response: { "ticker": "NVDA", "indicators": {...}, "signals": [...] }
```

---

## 7. Tech Stack

| Layer | Technology | Reason |
|-------|-----------|--------|
| Backend | FastAPI (Python) | Async, fast, auto-docs, same language as scanning logic |
| Frontend | Next.js (React) | Google OAuth built-in (NextAuth), SSR, modern |
| Database | SQLite | Single file, zero config, sufficient for single-user |
| Auth | Google OAuth + JWT | Simple, secure, no password management |
| Scheduling | Cron (system) | Reliable, simple, no extra dependency |
| Price Data | yFinance | Free, batch fetch, 6 months history |
| Technical Analysis | `ta` library + pandas + numpy | Industry standard indicators |
| News | Tavily (free tier, 1000/month) | Clean results, time filtering |
| LLM (synthesis) | Gemini 2.5 Flash | Free, good for summarization |
| Alerts | Telegram Bot API | Free, instant, rich formatting |
| Hosting | Oracle Cloud free tier | Always-on VM, $0/month |
| Charts (frontend) | Recharts or Lightweight Charts | Interactive, financial-grade |

### Cost Summary: $0/month
- Oracle VM: free forever
- yFinance: free
- Tavily: free (1000 searches/month, using ~16/day = 480/month)
- Gemini: free
- Telegram: free
- SQLite: free
- Domain (optional): ~$10/year

---

## 8. Configuration

### 8.1 settings.yaml

```yaml
scanner:
  schedule:
    times: ["08:00", "13:00"]
    timezone: "US/Eastern"
    days: ["mon", "tue", "wed", "thu", "fri"]

  thresholds:
    panic_sell:
      min_drop_pct: 5
      max_rsi: 30
      max_sector_correlation: 0.5  # stock drop vs sector drop
    short_squeeze:
      min_short_interest: 20
      min_days_to_cover: 5
      min_price_change_5d: 3
      min_volume_ratio: 2.0
    breakout:
      min_volume_ratio: 1.5
      rsi_range: [50, 70]
    news:
      lookback_hours: 24
      min_relevance_score: 0.7

  position_sizing:
    portfolio_value: 100000
    max_risk_per_trade_pct: 2
    max_positions: 10
    max_sector_exposure_pct: 30

alerts:
  telegram:
    bot_token: "${TELEGRAM_BOT_TOKEN}"
    admin_chat_id: "${TELEGRAM_CHAT_ID}"

auth:
  admin_email: "your.email@gmail.com"
  google_client_id: "${GOOGLE_CLIENT_ID}"
  jwt_secret: "${JWT_SECRET}"
```

---

## 9. Project Structure

```
marketpulse/
├── backend/
│   ├── src/
│   │   ├── scanner/
│   │   │   ├── price_scanner.py       # Batch fetch all tickers
│   │   │   ├── news_scanner.py        # Sector news via Tavily
│   │   │   ├── short_scanner.py       # Short interest data
│   │   │   └── run_scan.py            # Orchestrates full scan
│   │   ├── agents/
│   │   │   ├── panic_detector.py      # Mean reversion signals
│   │   │   ├── news_catalyst.py       # News-driven opportunities
│   │   │   ├── technical_agent.py     # Breakouts, MA crosses
│   │   │   ├── squeeze_detector.py    # Short squeeze candidates
│   │   │   ├── market_regime.py       # VIX, put/call, breadth
│   │   │   └── synthesis_agent.py     # Combines + filters + calculates levels
│   │   ├── api/
│   │   │   ├── main.py               # FastAPI app
│   │   │   ├── auth.py               # Google OAuth + JWT
│   │   │   ├── routes_signals.py     # Signal endpoints
│   │   │   ├── routes_admin.py       # User management
│   │   │   └── dependencies.py       # Auth middleware
│   │   ├── core/
│   │   │   ├── config.py             # YAML config loader
│   │   │   ├── models.py             # Dataclasses (Signal, SellAlert)
│   │   │   └── universe.py           # Sector/ticker definitions
│   │   ├── storage/
│   │   │   ├── database.py           # SQLite operations
│   │   │   └── migrations.py         # Schema creation
│   │   ├── alerts/
│   │   │   ├── telegram.py           # Send alerts
│   │   │   └── formatter.py          # Format signal → message
│   │   └── utils/
│   │       ├── indicators.py         # RSI, MACD, MA, volume
│   │       ├── levels.py             # Support/resistance/exit calc
│   │       └── position_sizing.py    # Risk management math
│   ├── tests/
│   ├── config/
│   │   └── settings.yaml
│   ├── data/
│   │   └── marketpulse.db
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx              # Dashboard (active signals)
│   │   │   ├── history/page.tsx      # Signal history + stats
│   │   │   ├── scan/page.tsx         # Manual scan trigger
│   │   │   └── admin/page.tsx        # User management
│   │   ├── components/
│   │   │   ├── SignalCard.tsx         # Single signal display
│   │   │   ├── StockChart.tsx        # Price chart with levels
│   │   │   └── StatsPanel.tsx        # Win rate, returns
│   │   └── lib/
│   │       ├── auth.ts               # NextAuth config
│   │       └── api.ts                # Backend API client
│   ├── package.json
│   └── next.config.js
│
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
└── README.md
```

---

## 10. Development Phases

### Phase 1: Scanner Core (Week 1)
- [ ] Project setup (Python, venv, config)
- [ ] Batch price fetching (yFinance, all 52 tickers, 6 months)
- [ ] Indicator calculations (RSI, MACD, MA50, MA200, volume avg)
- [ ] Panic sell detection logic
- [ ] SQLite schema + basic CRUD
- [ ] Console output of detected signals
- [ ] Unit tests for indicators and detection logic

### Phase 2: All Signal Types (Week 2)
- [ ] Tavily news integration (per-sector scanning)
- [ ] News catalyst detection (LLM classifies headlines)
- [ ] Short squeeze detection
- [ ] Technical breakout detection (MA cross, resistance break)
- [ ] Market regime assessment (VIX, put/call)
- [ ] Exit level calculator (stop-loss, targets)
- [ ] Position sizing calculator

### Phase 3: Synthesis + Alerts (Week 3)
- [ ] Synthesis agent (combine signals, filter noise, assign conviction)
- [ ] Active position monitoring (check targets/stops)
- [ ] Sell alert generation
- [ ] Telegram bot setup + alert formatting
- [ ] Scan logging
- [ ] Cron job setup (local first)

### Phase 4: FastAPI Backend (Week 4)
- [ ] FastAPI app with signal endpoints
- [ ] Google OAuth verification
- [ ] JWT token issuance
- [ ] Admin endpoints (user CRUD)
- [ ] Auth middleware
- [ ] Manual scan trigger endpoint
- [ ] Stats endpoint (win rate, returns)

### Phase 5: Next.js Frontend (Week 5-6)
- [ ] Next.js project setup
- [ ] NextAuth with Google provider
- [ ] Dashboard page (active signals as cards)
- [ ] Signal detail view (chart with entry/exit levels)
- [ ] History page with filters
- [ ] Stats panel (win rate, by signal type)
- [ ] Admin page (add/remove users)
- [ ] Manual scan trigger button

### Phase 6: Deployment (Week 7)
- [ ] Oracle Cloud VM setup
- [ ] Docker compose (backend + frontend)
- [ ] Cron job on VM
- [ ] Domain + HTTPS (optional)
- [ ] Monitoring (health check endpoint)

### Phase 7: Backtesting + Refinement (Ongoing)
- [ ] Run for 30 days, collect data
- [ ] Analyze signal accuracy by type
- [ ] Tune thresholds based on results
- [ ] Add/remove tickers based on signal quality
- [ ] Adjust position sizing based on win rate

---

## 11. Alert Templates

### New Buy Signal
```
🔥 [SIGNAL_TYPE] — TICKER at $XX.XX

📊 WHY (Conviction: HIGH):
  • Factor 1
  • Factor 2
  • Factor 3

📍 ENTRY: $XX.XX

🎯 EXIT TARGETS:
  🟢 T1: $XX.XX (+XX%) — Sell 1/3, move stop to breakeven
  🟡 T2: $XX.XX (+XX%) — Sell 1/3, move stop to T1
  🔴 T3: $XX.XX (+XX%) — Sell remaining

⛔ RISK:
  Stop-loss: $XX.XX (-XX%)
  Time stop: XX days (exit by DATE)
  Position: XXX shares ($X,XXX)
  Max loss: $X,XXX (2% of portfolio)
```

### Sell Alert (Target Hit)
```
🟢 TARGET HIT — TICKER

Target 1 reached: $XX.XX (+XX% from entry)
Entry was: $XX.XX on DATE

ACTION: Sell 1/3 of position, move stop to breakeven ($XX.XX)
Remaining targets: T2 $XX.XX, T3 $XX.XX
```

### Sell Alert (Stop-Loss)
```
⛔ STOP-LOSS — TICKER

Price hit $XX.XX (stop was $XX.XX)
Entry was: $XX.XX on DATE
Loss: -XX% ($XXX)

ACTION: Exit entire position
Lesson: [brief note on what happened]
```

### Daily Summary (No Signals)
```
✅ Market Scan Complete — 8:00 AM EST, May 16 2026

No new signals detected.

Market: SPY +0.3%, VIX 14.2 (low vol)
Active positions: 3 (MU +5%, PLTR +2%, AMD -1%)
Next catalyst: Fed minutes Wednesday 2PM

Have a good day. 🎯
```

---

## 12. Security Considerations

- API keys stored as environment variables, never in code
- JWT tokens expire after 24 hours
- Google OAuth verifies email domain
- Admin-only endpoints protected by role check
- Rate limiting on scan endpoints (prevent abuse)
- SQLite file not exposed via API (only structured data returned)
- Telegram bot token kept server-side only

---

## 13. Success Metrics (After 30 Days)

| Metric | Target |
|--------|--------|
| Signal accuracy (hit T1) | >60% |
| Stop-loss hit rate | <30% |
| Average return per signal | >5% |
| False signal rate | <20% |
| Scan reliability (no errors) | >99% |
| Alert delivery time | <5 seconds |

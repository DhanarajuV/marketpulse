# 🎯 MarketPulse — Proactive Market Intelligence Agent

## Overview

An autonomous market scanning system that runs twice daily (8AM & 1PM EST), analyzes 50+ stocks across 8 sectors, and alerts you only when it finds high-conviction opportunities.

**Philosophy**: Silence is golden. No signal = no alert. Only notify when something actionable is detected.

---

## Signal Types

### 1. Panic Sell Detection (Mean Reversion)
- Stock drops 5%+ on no fundamental bad news
- RSI < 30 (oversold) on fundamentally strong company
- Stock down significantly while its sector ETF is flat
- **Thesis**: Market overreaction → recovery in 1-2 weeks

### 2. News Catalyst
- Sector-wide catalyst (policy, earnings, macro)
- Company-specific positive catalyst on a dip
- Supply chain shifts benefiting specific companies
- **Thesis**: News creates tailwind that market hasn't fully priced in

### 3. Technical Breakout
- Stock breaks above resistance on high volume
- Golden cross (50-day MA crosses above 200-day MA)
- Cup and handle, bull flag patterns
- **Thesis**: Momentum + volume = trend continuation

### 4. Short Squeeze
- Short interest > 20% of float
- Days to cover > 5
- Price rising on high volume (shorts getting trapped)
- Retail buzz increasing (Reddit, StockTwits)
- **Thesis**: Forced covering creates snowball buying pressure

### 5. Market Regime
- VIX spike (fear = opportunity for contrarians)
- Sector rotation signals
- Put/call ratio extremes
- **Thesis**: Extreme fear/greed = mean reversion opportunity

---

## Alert Format (Every Signal)

```
🔥 [SIGNAL TYPE] — TICKER at $XX.XX

WHY:
  • [Evidence 1]
  • [Evidence 2]
  • [Evidence 3]

ENTRY: $XX.XX

EXIT TARGETS:
  🟢 Safe exit:   $XX.XX (+XX%) — [reasoning]
  🟡 Medium exit: $XX.XX (+XX%) — [reasoning]
  🔴 Peak target: $XX.XX (+XX%) — [reasoning]

RISK MANAGEMENT:
  ⛔ Stop-loss: $XX.XX (-XX%) — Thesis broken below here
  ⏰ Time stop: X days — No movement = exit
  💰 Position size: X shares ($X,XXX) for $XXXk portfolio
  📉 Max loss: $X,XXX (2% of portfolio)

STRATEGY:
  • Scale-out plan at each target
  • What to expect (volatility, timeline)
  • When thesis is invalidated

Conviction: LOW / MEDIUM / HIGH
```

---

## Sector Universe (~50 tickers)

| Sector | ETF | Top Stocks |
|--------|-----|-----------|
| Tech | QQQ | AAPL, MSFT, GOOGL, META, NVDA, CRM |
| Semiconductors | SMH | NVDA, AMD, AVGO, TSM, INTC, MU, QCOM |
| Energy | XLE | XOM, CVX, SLB, OXY, COP |
| Defense | ITA | LMT, RTX, NOC, GD, BA, PLTR |
| Healthcare | XLV | UNH, JNJ, LLY, PFE, ABBV, TMO |
| Financials | XLF | JPM, BAC, GS, V, MA, BRK-B |
| Consumer | XLY | AMZN, TSLA, HD, NKE, COST |
| Industrials | XLI | CAT, HON, UPS, DE, GE |

---

## Tech Stack

| Component | Technology | Cost |
|-----------|-----------|------|
| Scheduler | APScheduler (Python) or cron | Free |
| Price/Fundamentals | yFinance (batch fetch) | Free |
| Technical Analysis | `ta` library + pandas + numpy | Free |
| News | Tavily (1000/month) or NewsAPI (500/day) | Free |
| Sentiment/Synthesis | Gemini Flash or GPT-4o-mini | ~$0.10/day |
| Short Interest | yFinance `.info` + Finviz scraping | Free |
| Alerts | Telegram Bot API | Free |
| Dashboard | Streamlit (optional review UI) | Free |
| Storage | SQLite (signal history + backtesting) | Free |
| Hosting | Local machine or $5/month VPS | Free-$5 |

**Total daily cost**: ~$0.10-0.20 (2 scans × LLM synthesis calls)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 SCHEDULER (8AM & 1PM EST)                    │
└────────────────────────────┬────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────┐
│              DATA COLLECTION (parallel)                      │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Price/Volume │  │    News      │  │   Short      │      │
│  │  All 50 tkrs │  │  Per sector  │  │  Interest    │      │
│  │  (yFinance)  │  │  (Tavily)    │  │  (yFinance)  │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          └──────────────────┼──────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────┐
│              ANALYSIS AGENTS (parallel)                      │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Panic Sell   │  │   News       │  │  Technical   │      │
│  │ Detector     │  │  Catalyst    │  │  Breakout    │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │   Short      │  │   Market     │                        │
│  │  Squeeze     │  │   Regime     │                        │
│  └──────┬───────┘  └──────┬───────┘                        │
└─────────┼──────────────────┼────────────────────────────────┘
          └──────────────────┼─────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────┐
│              SYNTHESIS AGENT                                 │
│                                                             │
│  • Filter noise (only high-confidence signals)              │
│  • Calculate entry/exit/stop-loss levels                    │
│  • Position sizing based on portfolio                       │
│  • Assign conviction (requires 2+ confirming signals)       │
│  • Generate human-readable alert                            │
└────────────────────────────┬────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────┐
│              OUTPUT                                          │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │ Telegram │  │  SQLite  │  │Dashboard │                  │
│  │  Alert   │  │   Log    │  │(optional)│                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Exit Level Calculation Logic

### Stop-Loss
- Default: 20% below entry (hard max loss)
- Tighter: Just below recent support level
- Use whichever is TIGHTER (less loss)

### Exit Targets
- **Safe (Target 1)**: First resistance level above entry OR +15%
- **Medium (Target 2)**: 50-day MA if above, or next major resistance OR +25%
- **Peak (Target 3)**: Based on signal type:
  - Panic sell: Previous price before the drop
  - Short squeeze: Entry × (1 + short_interest × 2), capped at +50%
  - Breakout: Measured move (pattern height added to breakout point)

### Position Sizing
- Never risk more than 2% of portfolio on one trade
- Position size = (Portfolio × 0.02) / (Entry - Stop Loss)
- Example: $100k portfolio, $20 entry, $16 stop → 500 shares ($10k position)

### Scale-Out Strategy
- At Target 1: Sell 1/3, move stop to breakeven
- At Target 2: Sell 1/3, move stop to Target 1
- At Target 3: Sell remaining

---

## Development Phases

### Phase 1: Scanner Foundation (Week 1)
- [ ] Project setup, venv, config
- [ ] Batch price fetching (50 tickers, 6 months history)
- [ ] Technical indicators (RSI, MACD, MA50, MA200, volume avg)
- [ ] Panic sell detection (drop% + RSI + sector comparison)
- [ ] SQLite schema for signals
- [ ] Basic console output

### Phase 2: News + Sentiment (Week 2)
- [ ] Tavily integration for sector news
- [ ] LLM-based headline classification (bullish/bearish/neutral)
- [ ] News-catalyst detection
- [ ] Combine news + price signals

### Phase 3: Short Squeeze + Technical (Week 3)
- [ ] Short interest data collection
- [ ] Squeeze candidate detection
- [ ] Support/resistance calculation
- [ ] MA crossover detection
- [ ] Volume breakout detection

### Phase 4: Synthesis + Alerts (Week 4)
- [ ] Synthesis agent (combine all signals, filter noise)
- [ ] Exit level calculator
- [ ] Position sizing
- [ ] Telegram bot setup
- [ ] Alert formatting

### Phase 5: Scheduling + Dashboard (Week 5)
- [ ] APScheduler for 8AM/1PM EST runs
- [ ] Streamlit dashboard (signal history, active positions)
- [ ] Daily digest summary
- [ ] Backtesting framework (run signals against past data)

### Phase 6: Refinement (Ongoing)
- [ ] Track signal accuracy (did panic sells recover? did squeezes squeeze?)
- [ ] Tune thresholds based on results
- [ ] Add/remove tickers
- [ ] Pattern recognition improvements

---

## Key Design Principles

1. **No noise** — Only alert on high-conviction signals (2+ confirming factors)
2. **Always have an exit plan** — Every entry has defined stop-loss and targets
3. **Sector context** — Compare stock to its sector, not just absolute moves
4. **Time limits** — Don't hold forever. Time stop = discipline.
5. **Risk management first** — Position sizing ensures no single trade can hurt you badly
6. **Backtest everything** — Log all signals, verify accuracy over time
7. **Silence > false signals** — Better to miss an opportunity than act on noise

---

## Project Structure

```
marketpulse/
├── src/
│   ├── scanner/
│   │   ├── price_scanner.py       # Batch fetch prices + indicators
│   │   ├── news_scanner.py        # Sector news collection
│   │   └── short_scanner.py       # Short interest data
│   ├── agents/
│   │   ├── panic_detector.py      # Mean reversion signals
│   │   ├── news_catalyst.py       # News-driven opportunities
│   │   ├── technical_agent.py     # Breakouts, patterns, MA crosses
│   │   ├── squeeze_detector.py    # Short squeeze candidates
│   │   ├── market_regime.py       # Overall market sentiment
│   │   └── synthesis_agent.py     # Combines signals, calculates levels
│   ├── core/
│   │   ├── config.py
│   │   ├── models.py              # Signal dataclasses
│   │   └── universe.py            # Ticker lists by sector
│   ├── alerts/
│   │   ├── telegram_bot.py
│   │   └── formatter.py           # Alert message formatting
│   ├── storage/
│   │   ├── database.py            # SQLite operations
│   │   └── backtest.py            # Signal accuracy tracking
│   ├── utils/
│   │   ├── indicators.py          # RSI, MACD, MA calculations
│   │   ├── levels.py              # Support/resistance/exit calculation
│   │   └── position_sizing.py     # Risk management math
│   └── scheduler.py               # APScheduler entry point
├── tests/
├── config/
│   └── settings.yaml
├── data/
│   └── signals.db                 # SQLite database
├── requirements.txt
└── README.md
```

---

## Backtesting Plan

After 30 days of running, analyze:
- How many signals fired?
- What % hit Target 1? Target 2? Target 3?
- What % hit stop-loss?
- Average return per signal type
- Which signal types are most reliable?
- Which sectors produce best signals?

This data tells you whether to trust the system with real money.

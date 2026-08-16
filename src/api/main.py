"""FastAPI backend for MarketPulse."""
import os
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from src.storage.database import get_active_signals, get_signal_stats, get_signal_history
from src.scanner.run_scan import run_full_scan

load_dotenv()

API_KEY = os.getenv("MARKETPULSE_API_KEY", "")

app = FastAPI(title="MarketPulse API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Auth ---

def verify_api_key(x_api_key: str = Header(None)):
    """Simple API key authentication."""
    if not API_KEY:
        return  # No key configured = no auth (dev mode)
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


# --- Signal Endpoints ---

@app.get("/signals/active")
def active_signals(_=Depends(verify_api_key)):
    return get_active_signals()


@app.get("/signals/history")
def signal_history(days: int = 30, _=Depends(verify_api_key)):
    return get_signal_history(days)


@app.get("/signals/stats")
def stats(_=Depends(verify_api_key)):
    return get_signal_stats()


@app.post("/signals/scan")
def trigger_scan(_=Depends(verify_api_key)):
    """Trigger a manual full scan."""
    signals = run_full_scan()
    return {"signals_found": len(signals), "signals": signals}


@app.post("/signals/check")
def check_ticker_endpoint(body: dict, _=Depends(verify_api_key)):
    """Check a specific ticker."""
    import yfinance as yf
    import pandas as pd
    from src.scanner.price_scanner import calculate_indicators

    ticker = body.get("ticker", "").upper()
    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker required")

    data = yf.download(ticker, period="6mo", progress=False)
    if data.empty:
        raise HTTPException(status_code=404, detail=f"No data for {ticker}")

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    indicators = calculate_indicators(data)

    # Get short interest
    try:
        info = yf.Ticker(ticker).info
        indicators["short_interest"] = info.get("shortPercentOfFloat", 0) * 100
        indicators["short_ratio"] = info.get("shortRatio", 0)
    except Exception:
        indicators["short_interest"] = 0
        indicators["short_ratio"] = 0

    return {"ticker": ticker, "indicators": indicators}


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

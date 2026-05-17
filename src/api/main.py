"""FastAPI backend for MarketPulse."""
import os
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt, JWTError
from dotenv import load_dotenv

from src.storage.database import get_active_signals, get_signal_stats, get_conn
from src.scanner.run_scan import run_full_scan

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET", "marketpulse-dev-secret-change-in-prod")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "")

app = FastAPI(title="MarketPulse API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Auth ---

def create_token(email: str, role: str) -> str:
    payload = {
        "email": email,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=24),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def get_current_user(authorization: str = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return {"email": payload["email"], "role": payload["role"]}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return user


# --- Auth Endpoints ---

@app.post("/auth/login")
def login(body: dict):
    """Login with email. Admin gets admin role, others must be in users table."""
    email = body.get("email", "").lower()
    if not email:
        raise HTTPException(status_code=400, detail="Email required")

    if email == ADMIN_EMAIL.lower():
        return {"token": create_token(email, "admin"), "role": "admin"}

    # Check if user is authorized
    conn = get_conn()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()

    if not user:
        raise HTTPException(status_code=403, detail="Not authorized. Contact admin.")

    return {"token": create_token(email, user["role"]), "role": user["role"]}


@app.get("/auth/me")
def me(user: dict = Depends(get_current_user)):
    return user


# --- Admin Endpoints ---

@app.get("/admin/users")
def list_users(user: dict = Depends(require_admin)):
    conn = get_conn()
    rows = conn.execute("SELECT email, name, role, created_at FROM users").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.post("/admin/users")
def add_user(body: dict, user: dict = Depends(require_admin)):
    email = body.get("email", "").lower()
    name = body.get("name", "")
    if not email:
        raise HTTPException(status_code=400, detail="Email required")

    conn = get_conn()
    conn.execute("INSERT OR IGNORE INTO users (email, name, role) VALUES (?, ?, 'user')", (email, name))
    conn.commit()
    conn.close()
    return {"email": email, "name": name, "role": "user"}


@app.delete("/admin/users/{email}")
def remove_user(email: str, user: dict = Depends(require_admin)):
    conn = get_conn()
    conn.execute("DELETE FROM users WHERE email = ?", (email,))
    conn.commit()
    conn.close()
    return {"deleted": email}


# --- Signal Endpoints ---

@app.get("/signals/active")
def active_signals(user: dict = Depends(get_current_user)):
    return get_active_signals()


@app.get("/signals/history")
def signal_history(days: int = 30, user: dict = Depends(get_current_user)):
    conn = get_conn()
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    rows = conn.execute(
        "SELECT * FROM signals WHERE status != 'active' AND created_at > ? ORDER BY created_at DESC",
        (cutoff,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/signals/stats")
def stats(user: dict = Depends(get_current_user)):
    return get_signal_stats()


@app.post("/signals/scan")
def trigger_scan(user: dict = Depends(get_current_user)):
    """Trigger a manual full scan."""
    signals = run_full_scan()
    return {"signals_found": len(signals), "signals": signals}


@app.post("/signals/check")
def check_ticker_endpoint(body: dict, user: dict = Depends(get_current_user)):
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

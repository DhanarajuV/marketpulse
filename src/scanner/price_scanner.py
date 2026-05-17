import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD, SMAIndicator
from src.core.universe import get_all_tickers


def fetch_all_prices(period: str = "6mo") -> dict[str, pd.DataFrame]:
    """Batch fetch price data for all tickers."""
    tickers = get_all_tickers()
    data = yf.download(tickers, period=period, group_by="ticker", progress=False)

    result = {}
    for ticker in tickers:
        try:
            df = data[ticker].dropna()
            if not df.empty:
                result[ticker] = df
        except (KeyError, TypeError):
            continue

    print(f"Fetched data for {len(result)}/{len(tickers)} tickers")
    return result


def calculate_indicators(df: pd.DataFrame) -> dict:
    """Calculate technical indicators for a single ticker."""
    close = df["Close"]
    volume = df["Volume"]

    rsi = RSIIndicator(close, window=14).rsi().iloc[-1]
    ma_50 = SMAIndicator(close, window=50).sma_indicator().iloc[-1]
    ma_200 = SMAIndicator(close, window=200).sma_indicator().iloc[-1]
    macd_obj = MACD(close)
    macd_line = macd_obj.macd().iloc[-1]
    macd_signal = macd_obj.macd_signal().iloc[-1]

    current_price = close.iloc[-1]
    prev_close = close.iloc[-2]
    daily_change_pct = (current_price / prev_close - 1) * 100
    weekly_change_pct = (current_price / close.iloc[-5] - 1) * 100 if len(close) >= 5 else 0

    avg_volume_20 = volume.rolling(20).mean().iloc[-1]
    volume_ratio = volume.iloc[-1] / avg_volume_20 if avg_volume_20 > 0 else 1

    high_52w = close.tail(252).max() if len(close) >= 252 else close.max()
    low_52w = close.tail(252).min() if len(close) >= 252 else close.min()

    return {
        "price": current_price,
        "daily_change_pct": daily_change_pct,
        "weekly_change_pct": weekly_change_pct,
        "rsi": rsi,
        "ma_50": ma_50,
        "ma_200": ma_200,
        "macd": macd_line,
        "macd_signal": macd_signal,
        "volume_ratio": volume_ratio,
        "high_52w": high_52w,
        "low_52w": low_52w,
    }


if __name__ == "__main__":
    prices = fetch_all_prices()
    for ticker in ["AAPL", "NVDA", "MU"]:
        if ticker in prices:
            ind = calculate_indicators(prices[ticker])
            print(f"\n{ticker}: ${ind['price']:.2f} | RSI: {ind['rsi']:.1f} | Daily: {ind['daily_change_pct']:+.1f}% | Vol: {ind['volume_ratio']:.1f}x")

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import finnhub
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from src.core.universe import SECTORS, get_sector_for_ticker
from src.core.config import config

load_dotenv()

_finnhub_client = finnhub.Client(api_key=os.getenv("FINNHUB_API_KEY"))


def _get_company_news(ticker: str) -> list[dict]:
    """Get recent news for a specific ticker from Finnhub."""
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    try:
        news = _finnhub_client.company_news(ticker, _from=yesterday, to=today)
        return news[:5]  # Top 5 articles per ticker
    except Exception:
        return []


def _search_sector_news(sector_name: str, stocks: list[str]) -> str:
    """Get recent news for key stocks in a sector via Finnhub."""
    all_news = []

    # Check top 3 stocks in the sector for news
    for ticker in stocks[:3]:
        articles = _get_company_news(ticker)
        for article in articles:
            headline = article.get("headline", "")
            summary = article.get("summary", "")[:200]
            if headline:
                all_news.append(f"- [{ticker}] {headline}: {summary}")

    if not all_news:
        return ""

    return "\n".join(all_news[:10])  # Cap at 10 articles per sector


def _classify_news(news_text: str, sector: str) -> dict | None:
    """Use LLM to classify if news is a catalyst."""
    if not news_text.strip():
        return None

    llm = ChatGoogleGenerativeAI(model=config["llm"]["model"], temperature=config["llm"]["temperature"])
    prompt = f"""Analyze this news for the {sector} sector. Is there a clear positive catalyst that could move stocks up?

News:
{news_text}

Respond in this exact format (nothing else):
CATALYST: YES or NO
IMPACT: brief one-line description of the catalyst
TICKERS: comma-separated list of tickers most likely to benefit (from this list only)
CONFIDENCE: LOW, MEDIUM, or HIGH"""

    try:
        response = llm.invoke([
            SystemMessage(content="You are a financial news analyst. Be concise."),
            HumanMessage(content=prompt),
        ])
        text = response.content.strip()

        if "CATALYST: YES" not in text.upper():
            return None

        lines = text.strip().split("\n")
        result = {}
        for line in lines:
            if ":" in line:
                key, val = line.split(":", 1)
                result[key.strip().upper()] = val.strip()

        if "YES" not in result.get("CATALYST", ""):
            return None

        return {
            "impact": result.get("IMPACT", ""),
            "tickers": [t.strip() for t in result.get("TICKERS", "").split(",")],
            "confidence": result.get("CONFIDENCE", "MEDIUM"),
        }
    except Exception:
        return None


def detect_news_catalysts(all_indicators: dict) -> list[dict]:
    """Scan sector news for catalysts that could move stocks."""
    signals = []

    for sector_name, sector_data in SECTORS.items():
        news = _search_sector_news(sector_name, sector_data["stocks"])
        if not news:
            continue

        catalyst = _classify_news(news, sector_name)
        if not catalyst:
            continue

        # Generate signals for affected tickers
        for ticker in catalyst["tickers"]:
            if ticker not in all_indicators:
                continue

            indicators = all_indicators[ticker]
            price = indicators["price"]

            stop_loss = round(price * 0.90, 2)
            target_1 = round(price * 1.10, 2)
            target_2 = round(price * 1.20, 2)
            target_3 = round(price * 1.30, 2)

            signals.append({
                "ticker": ticker,
                "signal_type": "news_catalyst",
                "entry_price": round(price, 2),
                "stop_loss": stop_loss,
                "target_1": target_1,
                "target_2": target_2,
                "target_3": target_3,
                "time_stop_days": 21,
                "conviction": catalyst["confidence"],
                "reasoning": [
                    f"Sector: {sector_name}",
                    f"Catalyst: {catalyst['impact']}",
                    f"Current price: ${price:.2f}",
                ],
                "sector": sector_name,
            })

    return signals

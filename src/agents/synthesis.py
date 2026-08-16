"""Synthesize and rank signals using AI. Deduplicates, boosts multi-signal tickers,
and uses Gemini to pick the top signals when there are too many."""
import json
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from src.core.config import config

load_dotenv()

MAX_SIGNALS = 10


def _deduplicate_and_boost(all_signals: list[dict]) -> list[dict]:
    """Deduplicate signals for same ticker and boost conviction when multiple agents agree."""
    by_ticker = {}
    for signal in all_signals:
        ticker = signal["ticker"]
        if ticker not in by_ticker:
            by_ticker[ticker] = []
        by_ticker[ticker].append(signal)

    synthesized = []

    for ticker, signals in by_ticker.items():
        if len(signals) == 1:
            synthesized.append(signals[0])
            continue

        # Multiple signals for same ticker — merge them
        base = max(signals, key=lambda s: s["target_1"] / s["entry_price"])

        all_reasons = []
        signal_types = []
        for s in signals:
            signal_types.append(s["signal_type"])
            all_reasons.extend(s["reasoning"])

        base["conviction"] = "HIGH"
        base["reasoning"] = all_reasons
        base["reasoning"].insert(0, f"⚡ Multiple signals: {', '.join(signal_types)}")
        base["signal_type"] = " + ".join(sorted(set(signal_types)))
        base["_signal_count"] = len(signals)

        synthesized.append(base)

    return synthesized


def _ai_rank_signals(signals: list[dict]) -> list[dict]:
    """Use Gemini to rank signals and pick the best ones."""
    # Prepare signal summaries for the LLM
    signal_summaries = []
    for i, s in enumerate(signals):
        risk_reward = (s["target_1"] - s["entry_price"]) / (s["entry_price"] - s["stop_loss"]) if s["entry_price"] > s["stop_loss"] else 0
        summary = {
            "index": i,
            "ticker": s["ticker"],
            "signal_type": s["signal_type"],
            "conviction": s["conviction"],
            "entry_price": s["entry_price"],
            "stop_loss": s["stop_loss"],
            "target_1": s["target_1"],
            "risk_reward_ratio": round(risk_reward, 2),
            "sector": s["sector"],
            "reasoning": s["reasoning"][:3],  # First 3 reasons to keep prompt small
            "multi_signal": s.get("_signal_count", 1) > 1,
        }
        signal_summaries.append(summary)

    llm = ChatGoogleGenerativeAI(
        model=config["llm"]["model"],
        temperature=config["llm"]["temperature"],
    )

    prompt = f"""You are a quantitative trading signal analyst. You have {len(signal_summaries)} trading signals to rank.

Pick the TOP {MAX_SIGNALS} signals (or fewer if less than {MAX_SIGNALS} are good enough). Prioritize:
1. Risk/reward ratio (higher is better — at least 2:1)
2. Multi-signal confirmation (multiple detectors agreeing)
3. HIGH conviction signals
4. Sector diversification (don't pick 5 stocks from the same sector)
5. Avoid crowded trades (if too many signals in one sector, something might be off)

Signals:
{json.dumps(signal_summaries, indent=2)}

Respond with ONLY a JSON array of the selected signal indexes in priority order (best first).
Example: [3, 0, 7, 2, 5]

If fewer than {MAX_SIGNALS} signals are genuinely good, return fewer. Quality over quantity.
Return ONLY the JSON array, nothing else."""

    try:
        response = llm.invoke([
            SystemMessage(content="You are a quantitative analyst. Return only valid JSON. No explanation."),
            HumanMessage(content=prompt),
        ])

        # Parse the response — extract JSON array
        text = response.content.strip()
        # Handle markdown code blocks
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        selected_indexes = json.loads(text)

        # Validate indexes
        valid_indexes = [i for i in selected_indexes if isinstance(i, int) and 0 <= i < len(signals)]

        if not valid_indexes:
            # Fallback: return top MAX_SIGNALS by conviction
            return _fallback_rank(signals)

        return [signals[i] for i in valid_indexes[:MAX_SIGNALS]]

    except Exception as e:
        print(f"  ⚠️ AI ranking failed ({e}), using fallback")
        return _fallback_rank(signals)


def _fallback_rank(signals: list[dict]) -> list[dict]:
    """Fallback ranking if AI fails: sort by conviction and multi-signal, cap at MAX_SIGNALS."""
    conviction_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    signals.sort(key=lambda s: (
        conviction_order.get(s["conviction"], 2),
        -s.get("_signal_count", 1),
    ))
    return signals[:MAX_SIGNALS]


def synthesize_signals(all_signals: list[dict]) -> list[dict]:
    """Deduplicate, boost, and rank signals. Returns at most MAX_SIGNALS."""
    if not all_signals:
        return []

    # Step 1: Deduplicate and boost multi-signal tickers
    synthesized = _deduplicate_and_boost(all_signals)

    # Step 2: If within limit, return as-is
    if len(synthesized) <= MAX_SIGNALS:
        # Clean up internal fields
        for s in synthesized:
            s.pop("_signal_count", None)
        return synthesized

    # Step 3: Too many signals — use AI to pick the best ones
    print(f"  🤖 {len(synthesized)} signals found, using AI to pick top {MAX_SIGNALS}...")
    ranked = _ai_rank_signals(synthesized)

    # Clean up internal fields
    for s in ranked:
        s.pop("_signal_count", None)

    return ranked

"""DynamoDB storage for MarketPulse signals and positions."""
import os
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key, Attr

# DynamoDB config
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
SIGNALS_TABLE = os.getenv("DYNAMODB_SIGNALS_TABLE", "marketpulse-signals")

# Initialize DynamoDB resource
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
signals_table = dynamodb.Table(SIGNALS_TABLE)


def _to_decimal(value):
    """Convert float to Decimal for DynamoDB."""
    if value is None:
        return None
    return Decimal(str(value))


def _from_decimal(item: dict) -> dict:
    """Convert Decimal values back to float for API responses."""
    result = {}
    for key, value in item.items():
        if isinstance(value, Decimal):
            result[key] = float(value)
        elif isinstance(value, list):
            result[key] = [float(v) if isinstance(v, Decimal) else v for v in value]
        else:
            result[key] = value
    return result


def save_signal(signal: dict):
    """Save a new signal to DynamoDB."""
    time_stop = (datetime.now() + timedelta(days=signal["time_stop_days"])).isoformat()
    created_at = datetime.now().isoformat()

    item = {
        "signal_id": str(uuid.uuid4()),
        "ticker": signal["ticker"],
        "signal_type": signal["signal_type"],
        "conviction": signal["conviction"],
        "entry_price": _to_decimal(signal["entry_price"]),
        "stop_loss": _to_decimal(signal["stop_loss"]),
        "target_1": _to_decimal(signal["target_1"]),
        "target_2": _to_decimal(signal.get("target_2")),
        "target_3": _to_decimal(signal.get("target_3")),
        "time_stop_date": time_stop,
        "status": "active",
        "reasoning": signal["reasoning"],
        "sector": signal["sector"],
        "created_at": created_at,
    }

    # Remove None values (DynamoDB doesn't accept None)
    item = {k: v for k, v in item.items() if v is not None}

    signals_table.put_item(Item=item)


def get_active_signals() -> list[dict]:
    """Get all active (open) signals."""
    response = signals_table.scan(
        FilterExpression=Attr("status").eq("active")
    )
    return [_from_decimal(item) for item in response.get("Items", [])]


def close_signal(signal_id: str, close_price: float, status: str):
    """Close a signal (win, loss, or timeout)."""
    # Get the signal to calculate return
    response = signals_table.get_item(Key={"signal_id": signal_id})
    item = response.get("Item")

    if not item:
        return

    entry_price = float(item["entry_price"])
    return_pct = (close_price / entry_price - 1) * 100

    signals_table.update_item(
        Key={"signal_id": signal_id},
        UpdateExpression="SET #s = :status, close_price = :cp, close_date = :cd, return_pct = :rp",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={
            ":status": status,
            ":cp": _to_decimal(close_price),
            ":cd": datetime.now().isoformat(),
            ":rp": _to_decimal(return_pct),
        },
    )


def get_signal_stats() -> dict:
    """Get win/loss statistics."""
    # Scan for all closed signals
    response = signals_table.scan(
        FilterExpression=Attr("status").ne("active")
    )
    items = response.get("Items", [])

    total = len(items)
    wins = sum(1 for i in items if i.get("status") == "closed_win")
    losses = sum(1 for i in items if i.get("status") == "closed_loss")

    return {
        "total_closed": total,
        "wins": wins,
        "losses": losses,
        "win_rate": wins / total if total > 0 else 0,
    }


def get_signal_history(days: int = 30) -> list[dict]:
    """Get closed signals from the last N days."""
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()

    response = signals_table.scan(
        FilterExpression=Attr("status").ne("active") & Attr("created_at").gte(cutoff)
    )
    items = response.get("Items", [])
    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return [_from_decimal(item) for item in items]

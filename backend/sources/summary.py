from collections import defaultdict
from typing import List, Dict

from .column_guess import guess_columns


class SummaryError(Exception):
    pass


def compute_summary(rows: List[Dict]) -> dict:
    """Aggregates a source's synced rows into Home-dashboard-friendly
    numbers: revenue, orders, conversion rate, customers, avg order value,
    a channel breakdown, and a daily revenue/orders timeline. Uses
    best-effort column guessing rather than a manual mapping step, since
    Home is meant to be a quick glance, not a deep analysis."""
    if not rows:
        raise SummaryError("No synced data yet — run Sync first.")

    guess = guess_columns(list(rows[0].keys()))
    missing = [k for k, v in guess.items() if v is None]
    if missing:
        raise SummaryError(
            "Could not auto-detect column(s): " + ", ".join(missing) +
            ". Use Analytics → Use connected source to map columns manually."
        )

    user_col = guess["user_col"]
    ts_col = guess["timestamp_col"]
    channel_col = guess["channel_col"]
    revenue_col = guess["revenue_col"]

    total_revenue = 0.0
    users = set()
    converting_users = set()
    channel_totals: Dict[str, float] = defaultdict(float)
    daily: Dict[str, Dict[str, float]] = defaultdict(lambda: {"revenue": 0.0, "orders": 0})

    for r in rows:
        try:
            revenue = float(r.get(revenue_col) or 0)
        except (TypeError, ValueError):
            revenue = 0.0
        total_revenue += revenue

        uid = r.get(user_col)
        if uid:
            users.add(uid)
            if revenue > 0:
                converting_users.add(uid)

        channel = r.get(channel_col) or "unknown"
        channel_totals[channel] += revenue

        day = _to_day(r.get(ts_col))
        daily[day]["revenue"] += revenue
        daily[day]["orders"] += 1

    orders = len(rows)
    customers = len(users)
    avg_order_value = (total_revenue / orders) if orders else 0
    conversion_rate = (len(converting_users) / customers * 100) if customers else 0

    timeline = [
        {"date": day, "revenue": round(v["revenue"], 2), "orders": int(v["orders"])}
        for day, v in sorted(daily.items())
    ]

    channel_breakdown = [
        {"channel": ch, "revenue": round(v, 2)}
        for ch, v in sorted(channel_totals.items(), key=lambda x: -x[1])
    ]

    return {
        "total_revenue": round(total_revenue, 2),
        "orders": orders,
        "conversion_rate": round(conversion_rate, 1),
        "customers": customers,
        "avg_order_value": round(avg_order_value, 2),
        "channel_breakdown": channel_breakdown,
        "timeline": timeline,
    }


def _to_day(raw_ts) -> str:
    if not raw_ts:
        return "unknown"
    s = str(raw_ts)
    return s[:10] if len(s) >= 10 else s 
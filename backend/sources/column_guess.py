from typing import List, Optional, Dict


def guess_columns(columns: List[str]) -> Dict[str, Optional[str]]:
    """Best-effort guess of standard column roles from a source's raw
    column names, using common naming patterns — mirrors the guessing
    logic used for CSV uploads, so Home can show a summary without
    requiring the user to map columns manually first."""
    lower = {c.lower(): c for c in columns}

    def find(*candidates: str) -> Optional[str]:
        for cand in candidates:
            if cand in lower:
                return lower[cand]
        return None

    return {
        "user_col": find("user_id", "user", "customer_id", "uid", "client_id"),
        "timestamp_col": find("timestamp", "date", "time", "created_at", "order_date", "datetime"),
        "channel_col": find("channel", "source", "utm_source", "campaign"),
        "revenue_col": find("revenue", "amount", "total", "price", "sum", "order_total"),
    } 
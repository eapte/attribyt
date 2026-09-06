import socket
import requests
from typing import Tuple


def test_database(credentials: dict) -> Tuple[str, str | None]:
    """Checks whether the database is reachable. For the 'sqlite' test
    driver there's no host/port to check — we just confirm a query was
    provided. For real drivers (postgres/mysql, not implemented yet)
    this checks TCP reachability."""
    driver = credentials.get("driver", "sqlite")

    if driver == "sqlite":
        if not credentials.get("query", "").strip():
            return "error", "A query is required."
        return "connected", None

    host = credentials.get("host", "").strip()
    port_raw = credentials.get("port", "").strip()

    if not host or not port_raw:
        return "error", "Host and port are required."

    try:
        port = int(port_raw)
    except ValueError:
        return "error", "Port must be a number."

    try:
        with socket.create_connection((host, port), timeout=4):
            return "connected", None
    except Exception as e:
        return "error", f"Could not reach {host}:{port} ({e})"


def test_rest_api(credentials: dict) -> Tuple[str, str | None]:
    """Makes a real GET request to the given URL to confirm it responds."""
    url = credentials.get("url", "").strip()

    if not url:
        return "error", "Base URL is required."
    if not (url.startswith("http://") or url.startswith("https://")):
        return "error", "URL must start with http:// or https://"

    headers = {}
    token = credentials.get("token", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code >= 500:
            return "error", f"Endpoint returned server error ({resp.status_code})"
        return "connected", None
    except requests.exceptions.RequestException as e:
        return "error", f"Could not reach URL ({e})"


def test_webhook(credentials: dict) -> Tuple[str, str | None]:
    """Webhooks can't be tested outright — the external service pushes to us.
    We mark it as pending until the first event actually arrives (not yet implemented)."""
    return "pending", None 
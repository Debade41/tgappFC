import csv
import os
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

_lock = Lock()


def _log_path() -> Path:
    log_dir = os.getenv("LOG_DIR", "/data/logs")
    return Path(log_dir).expanduser().resolve() / "spins.csv"


def _format_user(user: dict) -> str:
    username = user.get("username")
    if username:
        return f"@{username}"
    first = user.get("first_name", "")
    last = user.get("last_name", "")
    name = " ".join(part for part in [first, last] if part)
    return name or str(user.get("id", ""))


def log_spin(user: dict, prize: str, already: bool) -> None:
    if not os.getenv("LOG_DIR"):
        return

    path = _log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    is_new = not path.exists()

    row = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": user.get("id", ""),
        "user_name": _format_user(user),
        "prize": prize,
        "already": "1" if already else "0",
    }

    with _lock, path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if is_new:
            writer.writeheader()
        writer.writerow(row)

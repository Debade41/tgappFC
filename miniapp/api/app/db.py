import os
import sqlite3
from pathlib import Path
from threading import Lock

DB_PATH = Path(os.getenv("DB_PATH", Path(__file__).resolve().parent / "wheel.db"))

_lock = Lock()
_conn = sqlite3.connect(DB_PATH, check_same_thread=False)
_conn.row_factory = sqlite3.Row


def init_db() -> None:
    with _lock:
        _conn.execute(
            """
            CREATE TABLE IF NOT EXISTS spins (
                telegram_id INTEGER PRIMARY KEY,
                prize TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        _conn.commit()


def get_spin(telegram_id: int):
    with _lock:
        cur = _conn.execute(
            "SELECT telegram_id, prize, created_at FROM spins WHERE telegram_id = ?",
            (telegram_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def set_spin(telegram_id: int, prize: str, created_at: str) -> None:
    with _lock:
        _conn.execute(
            "INSERT OR REPLACE INTO spins (telegram_id, prize, created_at) VALUES (?, ?, ?)",
            (telegram_id, prize, created_at),
        )
        _conn.commit()

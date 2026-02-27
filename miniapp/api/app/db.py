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
        _conn.execute(
            """
            CREATE TABLE IF NOT EXISTS spin_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                prize TEXT NOT NULL,
                created_at TEXT NOT NULL,
                month_id TEXT NOT NULL
            )
            """
        )
        _conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_spin_attempts_user_month ON spin_attempts (telegram_id, month_id)"
        )
        _conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_spin_attempts_user_id ON spin_attempts (telegram_id, id DESC)"
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


def add_spin_attempt(telegram_id: int, prize: str, created_at: str, month_id: str) -> None:
    with _lock:
        _conn.execute(
            "INSERT INTO spin_attempts (telegram_id, prize, created_at, month_id) VALUES (?, ?, ?, ?)",
            (telegram_id, prize, created_at, month_id),
        )
        _conn.execute(
            "INSERT OR REPLACE INTO spins (telegram_id, prize, created_at) VALUES (?, ?, ?)",
            (telegram_id, prize, created_at),
        )
        _conn.commit()


def count_spins_for_month(telegram_id: int, month_id: str) -> int:
    with _lock:
        row = _conn.execute(
            "SELECT COUNT(1) AS c FROM spin_attempts WHERE telegram_id = ? AND month_id = ?",
            (telegram_id, month_id),
        ).fetchone()
        return int(row["c"]) if row else 0


def get_last_spin(telegram_id: int):
    with _lock:
        row = _conn.execute(
            """
            SELECT telegram_id, prize, created_at
            FROM spin_attempts
            WHERE telegram_id = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (telegram_id,),
        ).fetchone()
        if row:
            return dict(row)

        # legacy fallback (old single-spin format)
        legacy = _conn.execute(
            "SELECT telegram_id, prize, created_at FROM spins WHERE telegram_id = ?",
            (telegram_id,),
        ).fetchone()
        return dict(legacy) if legacy else None

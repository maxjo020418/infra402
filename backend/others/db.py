import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator, Optional

# Simple SQLite-backed store for container leases and ownership
DB_PATH = Path(os.getenv("LEASE_DB_PATH", "data/leases.db"))


def _ensure_db() -> None:
    """Create the database and schema if it does not exist."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS container_leases (
                lease_id TEXT PRIMARY KEY,
                ctid TEXT NOT NULL,
                owner_wallet TEXT NOT NULL,
                network TEXT NOT NULL,
                status TEXT NOT NULL,
                expires_at TEXT,
                created_at TEXT NOT NULL
            );
            """
        )
        conn.commit()


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """Yield a connection with row access enabled."""
    _ensure_db()
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def record_container_lease(
    *,
    lease_id: str,
    ctid: str,
    owner_wallet: str,
    network: str,
    status: str,
    expires_at: Optional[str],
) -> None:
    """Persist container lease ownership info."""
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO container_leases
                (lease_id, ctid, owner_wallet, network, status, expires_at, created_at)
            VALUES
                (:lease_id, :ctid, :owner_wallet, :network, :status, :expires_at, :created_at);
            """,
            {
                "lease_id": lease_id,
                "ctid": ctid,
                "owner_wallet": owner_wallet.lower(),
                "network": network,
                "status": status,
                "expires_at": expires_at,
                "created_at": datetime.utcnow().isoformat(),
            },
        )
        conn.commit()


def get_owner_by_lease_id(lease_id: str) -> Optional[str]:
    """Return the owning wallet for a given lease id."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT owner_wallet FROM container_leases WHERE lease_id = ?;",
            (lease_id,),
        ).fetchone()
        return row["owner_wallet"] if row else None


def get_owner_by_ctid(ctid: str) -> Optional[str]:
    """Return the owning wallet for a given container id."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT owner_wallet FROM container_leases WHERE ctid = ?;",
            (ctid,),
        ).fetchone()
        return row["owner_wallet"] if row else None

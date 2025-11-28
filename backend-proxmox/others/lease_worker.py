import asyncio
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI

from others.db import (
    lease_is_expired,
    list_all_leases,
    update_lease_status,
)
from others.pve_client import PVEError, get_config, stop_lxc


async def _refresh_leases_loop(poll_seconds: int = 60) -> None:
    """Periodic task: refresh lease statuses and stop expired containers."""
    cfg = get_config()
    while True:
        now = datetime.now(timezone.utc)
        leases = list_all_leases()
        for lease in leases:
            expired = lease_is_expired(lease, now)
            desired_status = "expired" if expired else "active"
            current_status: Optional[str] = lease.get("status")

            if current_status != desired_status:
                update_lease_status(lease["lease_id"], desired_status)

            if expired and current_status != "expired":
                try:
                    await stop_lxc(cfg, vmid=lease["ctid"])
                except PVEError as exc:
                    # Avoid crashing the worker; log and continue.
                    print(f"[lease-worker] Failed to stop expired CT {lease['ctid']}: {exc}")

        await asyncio.sleep(poll_seconds)


def start_lease_worker(app: FastAPI) -> None:
    """Start background task when app starts."""
    loop = asyncio.get_running_loop()
    app.state.lease_worker = loop.create_task(_refresh_leases_loop())


async def stop_lease_worker(app: FastAPI) -> None:
    """Cancel worker on shutdown if running."""
    task = getattr(app.state, "lease_worker", None)
    if task:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

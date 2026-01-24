from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from others.auth import get_request_wallet
from others.db import list_leases_by_owner
from others.pve_client import PVEError, get_config, get_lxc_status, get_node_status

router = APIRouter(
    prefix="/stats",
    tags=["stats"],
)


class UsageStats(BaseModel):
    used: int | None = None
    total: int | None = None
    free: int | None = None
    pct: float | None = None


class CpuStats(BaseModel):
    usage: float | None = None
    cores: int | None = None
    pct: float | None = None


class NodeStatsResponse(BaseModel):
    node: str
    cpu: CpuStats
    memory: UsageStats
    disk: UsageStats


class LxcStats(BaseModel):
    leaseId: str
    ctid: str
    sku: str | None = None
    status: str | None = None
    cpu: CpuStats | None = None
    memory: UsageStats | None = None
    disk: UsageStats | None = None
    error: str | None = None


def _usage(used: int | None, total: int | None) -> UsageStats:
    free = None
    pct = None
    if used is not None and total:
        free = max(total - used, 0)
        pct = (used / total) * 100.0
    return UsageStats(used=used, total=total, free=free, pct=pct)


def _cpu(usage: float | None, cores: int | None) -> CpuStats:
    pct = None
    if usage is not None:
        pct = usage * 100.0
    return CpuStats(usage=usage, cores=cores, pct=pct)


@router.get("/node", response_model=NodeStatsResponse)
async def get_node_stats(request: Request) -> NodeStatsResponse:
    _ = get_request_wallet(request)
    cfg = get_config()
    try:
        data = await get_node_status(cfg)
    except PVEError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"PVE error: {exc}",
        ) from exc

    return NodeStatsResponse(
        node=cfg.node,
        cpu=_cpu(data.get("cpu"), data.get("maxcpu")),
        memory=_usage(data.get("mem"), data.get("maxmem")),
        disk=_usage(data.get("disk"), data.get("maxdisk")),
    )


@router.get("/lxc", response_model=list[LxcStats])
async def get_lxc_stats(request: Request) -> list[LxcStats]:
    owner_wallet = get_request_wallet(request)
    leases = list_leases_by_owner(owner_wallet)
    cfg = get_config()
    results: list[LxcStats] = []

    for lease in leases:
        ctid = str(lease.get("ctid"))
        stats = None
        error = None
        try:
            stats = await get_lxc_status(cfg, vmid=ctid)
        except PVEError as exc:
            error = str(exc)

        lease_id = lease.get("lease_id") or ""
        sku = lease.get("sku")

        results.append(
            LxcStats(
                leaseId=lease_id,
                ctid=ctid,
                sku=sku,
                status=stats.get("status") if stats else None,
                cpu=_cpu(stats.get("cpu") if stats else None, stats.get("cpus") if stats else None),
                memory=_usage(stats.get("mem") if stats else None, stats.get("maxmem") if stats else None),
                disk=_usage(stats.get("disk") if stats else None, stats.get("maxdisk") if stats else None),
                error=error,
            )
        )

    return results

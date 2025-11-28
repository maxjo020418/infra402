import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

from others.types import *
from others.db import (
    get_owner_by_ctid,
    get_lease_by_ctid,
    lease_is_expired,
    record_container_lease,
    update_lease_expiration,
)
from others.pve_client import (
    PVEError,
    create_lxc,
    create_vnc_proxy,
    get_config,
    get_next_vmid,
    get_lxc_status,
    run_command,
    start_lxc,
    get_access_ticket,
    build_console_url,
)
from x402.types import VerifyResponse

router = APIRouter(
    prefix="/lease",
    tags=["lease"],
)


class ExecRequest(BaseModel):
    command: str
    extraArgs: list[str] | None = None


class ExecResponse(BaseModel):
    ctid: str
    upid: str
    output: str


class ConsoleRequest(BaseModel):
    consoleType: str | None = "vnc"  # LXC supports VNC; SPICE not typical for LXC.


class ConsoleResponse(BaseModel):
    ctid: str
    host: str
    port: int
    ticket: str
    user: str
    cert: str | None = None
    websocket: int | None = None
    proxy: str | None = None
    consoleUrl: str | None = None
    authCookie: str | None = None


class RenewLeaseRequest(BaseModel):
    runtimeMinutes: int = Field(gt=0)


NETWORK = os.getenv("NETWORK", "base-sepolia")


@router.post("/container", response_model=LeaseResponse)
async def container(request_body: LeaseRequest, request: Request) -> LeaseResponse:
    """Lease an LXC container and persist ownership to SQLite."""
    verify: VerifyResponse | None = getattr(request.state, "verify_response", None)
    if verify is None or not verify.payer:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Missing payment verification",
        )

    owner_wallet = verify.payer

    cfg = get_config()

    hostname = request_body.hostname or f"{request_body.sku}-{uuid4().hex[:6]}"
    try:
        vmid = await get_next_vmid(cfg)
        await create_lxc(
            cfg,
            vmid=vmid,
            hostname=hostname,
            cores=request_body.cores,
            memory_mb=request_body.memoryMB,
            disk_gb=request_body.diskGB,
            password=request_body.password,
            start=True,
        )
    except PVEError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"PVE error: {exc}",
        ) from exc

    lease_response = build_lease_response(request_body)
    lease_response.ownerWallet = owner_wallet
    lease_response.ctid = vmid

    record_container_lease(
        lease_id=lease_response.leaseId,
        ctid=vmid,
        owner_wallet=owner_wallet,
        network=NETWORK,
        status=lease_response.status,
        expires_at=lease_response.expiresAt,
    )

    return lease_response


def _require_owner(ctid: str, payer: str) -> None:
    owner = get_owner_by_ctid(ctid)
    if not owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No lease found for this container",
        )
    if owner.lower() != payer.lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized for this container",
        )


def _require_active_lease(ctid: str, payer: str) -> dict:
    lease = get_lease_by_ctid(ctid)
    if not lease:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No lease found for this container",
        )
    if lease["owner_wallet"].lower() != payer.lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized for this container",
        )
    if lease_is_expired(lease):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Lease has expired",
        )
    return lease


def _get_verified_payer(request: Request) -> str:
    verify: VerifyResponse | None = getattr(request.state, "verify_response", None)
    if verify is None or not verify.payer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing payment verification",
        )
    return verify.payer


# @router.post("/{ctid}/command", response_model=ExecResponse)
# async def exec_command(ctid: str, body: ExecRequest, request: Request) -> ExecResponse:
#     payer = _get_verified_payer(request)
#     _require_active_lease(ctid, payer)
#     cfg = get_config()

#     try:
#         result = await run_command(cfg, vmid=ctid, command=body.command, extra_args=body.extraArgs)
#     except PVEError as exc:
#         raise HTTPException(
#             status_code=status.HTTP_502_BAD_GATEWAY,
#             detail=f"PVE error: {exc}",
#         ) from exc

#     return ExecResponse(ctid=ctid, upid=result["upid"], output=result["output"])


# @router.post("/{ctid}/console", response_model=ConsoleResponse)
# async def console(ctid: str, body: ConsoleRequest, request: Request, response: Response) -> ConsoleResponse:
#     payer = _get_verified_payer(request)
#     _require_active_lease(ctid, payer)
#     cfg = get_config()

#     if body.consoleType not in (None, "vnc", "spice"):
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Unsupported console type",
#         )

#     try:
#         access_ticket = await get_access_ticket(cfg)
#         data = await create_vnc_proxy(cfg, vmid=ctid)
#         if not data.get("ticket"):
#             raise PVEError("VNC proxy did not return a ticket")
#     except PVEError as exc:
#         raise HTTPException(
#             status_code=status.HTTP_502_BAD_GATEWAY,
#             detail=f"PVE error: {exc}",
#         ) from exc

#     console_url = build_console_url(cfg, vmid=ctid, vncticket=data.get("ticket"))
#     auth_cookie = access_ticket.get("ticket")
#     if auth_cookie:
#         response.set_cookie(
#             "PVEAuthCookie",
#             auth_cookie,
#             domain=(cfg.host.split("//")[-1].split(":")[0]),
#             secure=True,
#             httponly=True,
#             samesite="lax",
#         )

#     return ConsoleResponse(
#         ctid=ctid,
#         host=cfg.host,
#         port=int(data.get("port")),
#         ticket=data.get("ticket"),
#         user=data.get("user"),
#         cert=data.get("cert"),
#         websocket=data.get("websocket"),
#         proxy=data.get("proxy"),
#         consoleUrl=console_url,
#         authCookie=auth_cookie,
#     )


@router.post("/{ctid}/renew", response_model=LeaseResponse)
async def renew_lease(ctid: str, body: RenewLeaseRequest, request: Request) -> LeaseResponse:
    payer = _get_verified_payer(request)
    lease = get_lease_by_ctid(ctid)
    if not lease:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No lease found for this container",
        )
    if lease["owner_wallet"].lower() != payer.lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized for this container",
        )

    now = datetime.now(timezone.utc)
    expires_at = lease.get("expires_at")
    base_time = now
    if expires_at:
        try:
            existing_expiration = datetime.fromisoformat(expires_at)
            if existing_expiration.tzinfo is None:
                existing_expiration = existing_expiration.replace(tzinfo=timezone.utc)
            base_time = max(existing_expiration, now)
        except ValueError:
            base_time = now

    new_expires_at = base_time + timedelta(minutes=body.runtimeMinutes)

    cfg = get_config()
    try:
        status_resp = await get_lxc_status(cfg, vmid=ctid)
    except PVEError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"PVE error: {exc}",
        ) from exc

    if status_resp.get("status") != "running":
        try:
            await start_lxc(cfg, vmid=ctid)
        except PVEError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"PVE error: {exc}",
            ) from exc

    update_lease_expiration(lease["lease_id"], new_expires_at.isoformat(), status="active")

    return LeaseResponse(
        leaseId=lease["lease_id"],
        status="active",
        ctid=ctid,
        expiresAt=new_expires_at.isoformat(),
        message=f"Lease renewed for {body.runtimeMinutes} minutes.",
        ownerWallet=lease.get("owner_wallet"),
    )

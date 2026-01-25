from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel

from others.pve_client import (
    PVEError,
    create_vnc_proxy,
    get_config,
    get_lxc_status,
    run_command,
    get_access_ticket,
    build_console_url,
)
from .lease import (
    _get_verified_payer,
    _require_active_lease,
    ConsoleRequest,
    ConsoleResponse,
    ExecRequest,
    ExecResponse,
)

router = APIRouter(
    prefix="/management",
    tags=["management"],
)


@router.post("/exec/{ctid}", response_model=ExecResponse)
async def exec_command(ctid: str, body: ExecRequest, request: Request) -> ExecResponse:
    payer = _get_verified_payer(request)
    _require_active_lease(ctid, payer)
    cfg = get_config()

    try:
        result = await run_command(cfg, vmid=ctid, command=body.command, extra_args=body.extraArgs)
    except PVEError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"PVE error: {exc}",
        ) from exc

    return ExecResponse(ctid=ctid, upid=result["upid"], output=result["output"])


@router.post("/console/{ctid}", response_model=ConsoleResponse)
async def console(ctid: str, body: ConsoleRequest, request: Request, response: Response) -> ConsoleResponse:
    payer = _get_verified_payer(request)
    _require_active_lease(ctid, payer)
    cfg = get_config()

    if body.consoleType not in (None, "vnc", "spice"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported console type",
        )

    try:
        access_ticket = await get_access_ticket(cfg)
        data = await create_vnc_proxy(cfg, vmid=ctid)
        if not data.get("ticket"):
            raise PVEError("VNC proxy did not return a ticket")
    except PVEError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"PVE error: {exc}",
        ) from exc

    console_url = build_console_url(cfg, vmid=ctid, vncticket=data.get("ticket"))
    auth_cookie = access_ticket.get("ticket")
    if auth_cookie:
        response.set_cookie(
            "PVEAuthCookie",
            auth_cookie,
            domain=(cfg.host.split("//")[-1].split(":")[0]),
            secure=True,
            httponly=True,
            samesite="lax",
        )

    return ConsoleResponse(
        ctid=ctid,
        host=cfg.host,
        port=int(data.get("port")),
        ticket=data.get("ticket"),
        user=data.get("user"),
        cert=data.get("cert"),
        websocket=data.get("websocket"),
        proxy=data.get("proxy"),
        consoleUrl=console_url,
        authCookie=auth_cookie,
    )


class ManagedContainer(BaseModel):
    leaseId: str
    ctid: str
    status: str
    expiresAt: str | None = None
    network: str
    createdAt: str
    vmStatus: dict | None = None


@router.get("/list", response_model=list[ManagedContainer])
async def list_containers(request: Request) -> list[ManagedContainer]:
    payer = _get_verified_payer(request)
    from others.db import list_leases_by_owner  # local import to avoid circular

    leases = list_leases_by_owner(payer)
    cfg = get_config()
    results: list[ManagedContainer] = []

    for lease in leases:
        vm_status = None
        try:
            vm_status = await get_lxc_status(cfg, vmid=lease["ctid"])
        except PVEError:
            vm_status = None

        results.append(
            ManagedContainer(
                leaseId=lease["lease_id"],
                ctid=lease["ctid"],
                status=lease["status"],
                expiresAt=lease.get("expires_at"),
                network=lease.get("network"),
                createdAt=lease.get("created_at"),
                vmStatus=vm_status,
            )
        )

    return results

import asyncio
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, quote
import json

import httpx


class PVEError(Exception):
    pass


@dataclass
class PVEConfig:
    host: str
    token_id: str
    token_secret: str
    node: str
    storage: str
    os_template: str
    verify_ssl: bool
    root_password: Optional[str] = None


def get_config() -> PVEConfig:
    host = os.getenv("PVE_HOST")
    token_id = os.getenv("PVE_TOKEN_ID")
    token_secret = os.getenv("PVE_TOKEN_SECRET")
    node = os.getenv("PVE_NODE")
    storage = os.getenv("PVE_STORAGE")
    os_template = os.getenv("PVE_OS_TEMPLATE")
    root_password = os.getenv("PVE_ROOT_PASSWORD")
    verify_ssl = os.getenv("PVE_VERIFY_SSL", "true").lower() != "false"

    missing = [
        name
        for name, value in [
            ("PVE_HOST", host),
            ("PVE_TOKEN_ID", token_id),
            ("PVE_TOKEN_SECRET", token_secret),
            ("PVE_NODE", node),
            ("PVE_STORAGE", storage),
            ("PVE_OS_TEMPLATE", os_template),
        ]
        if not value
    ]
    if missing:
        raise PVEError(f"Missing required PVE env vars: {', '.join(missing)}")

    return PVEConfig(
        host=host.rstrip("/"),
        token_id=token_id,
        token_secret=token_secret,
        node=node,
        storage=storage,
        os_template=os_template,
        verify_ssl=verify_ssl,
        root_password=root_password,
    )


# async def _request(
#     cfg: PVEConfig,
#     method: str,
#     path: str,
#     *,
#     params: Optional[Dict[str, Any]] = None,
#     data: Optional[Any] = None,
# ) -> Any:
#     url = urljoin(cfg.host, f"/api2/json{path}")
#     headers = {
#         "Authorization": f"PVEAPIToken={cfg.token_id}={cfg.token_secret}",
#     }
#     async with httpx.AsyncClient(verify=cfg.verify_ssl, timeout=30) as client:
#         resp = await client.request(method, url, params=params, data=data, headers=headers)
#         if resp.status_code >= 400:
#             raise PVEError(f"PVE request failed {resp.status_code}: {resp.text}")
#         payload = resp.json()
#         return payload
async def _request(
    cfg: PVEConfig,
    method: str,
    path: str,
    *,
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Any] = None,
) -> Any:
    url = urljoin(cfg.host, f"/api2/json{path}")
    headers = {
        "Authorization": f"PVEAPIToken={cfg.token_id}={cfg.token_secret}",
    }
    async with httpx.AsyncClient(verify=cfg.verify_ssl, timeout=30) as client:
        resp = await client.request(method, url, params=params, data=data, headers=headers)
        print("Request:", url)
        print("PVE DEBUG:", resp.status_code, url)
        print("Content-Type:", resp.headers.get("content-type"))
        print("Body preview:", resp.text[:500])

        if resp.status_code >= 400:
            raise PVEError(f"PVE request failed {resp.status_code}: {resp.text}")

        try:
            payload = resp.json()
        except json.JSONDecodeError as e:
            raise PVEError(
                f"PVE returned non-JSON body for {url}: "
                f"status={resp.status_code}, body={resp.text[:200]}"
            ) from e

        return payload


async def get_next_vmid(cfg: PVEConfig) -> str:
    payload = await _request(cfg, "GET", "/cluster/nextid")
    return str(payload.get("data"))


async def wait_for_task(cfg: PVEConfig, upid: str, timeout_seconds: int = 180) -> Dict[str, Any]:
    deadline = asyncio.get_event_loop().time() + timeout_seconds
    encoded_upid = quote(upid, safe="")
    while True:
        status_payload = await _request(
            cfg,
            "GET",
            f"/nodes/{cfg.node}/tasks/{encoded_upid}/status",
        )
        data = status_payload.get("data") or {}
        if data.get("status") == "stopped":
            if data.get("exitstatus") == "OK":
                return data
            raise PVEError(f"Task failed: {data.get('exitstatus')}")
        if asyncio.get_event_loop().time() > deadline:
            raise PVEError("Task did not finish before timeout")
        await asyncio.sleep(2)


async def create_lxc(
    cfg: PVEConfig,
    *,
    vmid: str,
    hostname: str,
    cores: int,
    memory_mb: int,
    disk_gb: int,
    start: bool = True,
) -> Dict[str, Any]:
    if not cfg.root_password:
        raise PVEError("PVE_ROOT_PASSWORD env var is required to create LXC containers")

    payload = {
        "vmid": vmid,
        "hostname": hostname,
        "cores": cores,
        "memory": memory_mb,
        "ostemplate": cfg.os_template,
        "rootfs": f"{cfg.storage}:{disk_gb}",
        "storage": cfg.storage,
        "password": cfg.root_password,
        "start": 1 if start else 0,
        "unprivileged": 1,
    }

    create_payload = await _request(cfg, "POST", f"/nodes/{cfg.node}/lxc", data=payload)
    upid = create_payload.get("data")
    task_status = await wait_for_task(cfg, upid)
    return {"upid": upid, "task_status": task_status}


async def run_command(
    cfg: PVEConfig, *, vmid: str, command: str, extra_args: Optional[List[str]] = None
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"command": command, "tty": "0"}
    if extra_args:
        # Send repeated extra-args keys by using a list value for urlencoding.
        payload["extra-args"] = extra_args

    resp = await _request(
        cfg,
        "POST",
        f"/nodes/{cfg.node}/lxc/{vmid}/exec",
        data=payload,
    )
    upid = resp.get("data")
    status = await wait_for_task(cfg, upid)
    log_resp = await _request(
        cfg,
        "GET",
        f"/nodes/{cfg.node}/tasks/{quote(upid, safe='')}/log",
        params={"start": 0},
    )
    logs = [entry.get("t", "") for entry in (log_resp.get("data") or [])]
    return {"upid": upid, "status": status, "output": "\n".join(logs).strip()}


async def create_vnc_proxy(cfg: PVEConfig, *, vmid: str) -> Dict[str, Any]:
    resp = await _request(
        cfg,
        "POST",
        f"/nodes/{cfg.node}/lxc/{vmid}/vncproxy",
        data={"websocket": 1},
    )
    data = resp.get("data") or {}
    return data


async def stop_lxc(cfg: PVEConfig, *, vmid: str) -> str:
    """Stop a running LXC container."""
    resp = await _request(
        cfg,
        "POST",
        f"/nodes/{cfg.node}/lxc/{vmid}/status/stop",
    )
    return resp.get("data", "")


async def get_lxc_status(cfg: PVEConfig, *, vmid: str) -> Dict[str, Any]:
    """Fetch current LXC status."""
    resp = await _request(
        cfg,
        "GET",
        f"/nodes/{cfg.node}/lxc/{vmid}/status/current",
    )
    return resp.get("data") or {}

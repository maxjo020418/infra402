import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from x402.fastapi.middleware import require_payment
from x402.types import PaywallConfig

# Load environment variables
load_dotenv()

# Get configuration from environment
NETWORK = os.getenv("NETWORK", "base-sepolia")
ADDRESS = os.getenv("ADDRESS")
CDP_CLIENT_KEY = os.getenv("CDP_CLIENT_KEY")

if not ADDRESS:
    raise ValueError("Missing required environment variables")

app = FastAPI()

# Allow local frontend to call this API directly
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory (used by example assets)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Apply payment middleware to the lease endpoints used by the frontend
app.middleware("http")(
    require_payment(
        price="$0.01",
        pay_to_address=ADDRESS,
        path=[
            "/leases/container",
            "/leases/vm",
            "/leases/gpu",
            "/premium/content",
        ],
        network=NETWORK,
        paywall_config=PaywallConfig(
            cdp_client_key=CDP_CLIENT_KEY or "",
            app_name="infra402 backend",
            app_logo="/static/x402.png",
        ),
    )
)


class LeaseRequest(BaseModel):
    sku: str
    runtimeMinutes: int
    requester: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None


class LeaseResponse(BaseModel):
    leaseId: str
    status: str
    expiresAt: Optional[str] = None
    message: Optional[str] = None


def _build_lease_response(request: LeaseRequest) -> LeaseResponse:
    lease_id = f"{request.sku}-{uuid4().hex[:8]}"
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=request.runtimeMinutes
    )
    return LeaseResponse(
        leaseId=lease_id,
        status="active",
        expiresAt=expires_at.isoformat(),
        message=f"Lease for {request.sku} granted for {request.runtimeMinutes} minutes.",
    )


@app.post("/leases/container", response_model=LeaseResponse)
async def lease_container(request: LeaseRequest) -> LeaseResponse:
    """Lease ephemeral container capacity."""
    return _build_lease_response(request)


@app.post("/leases/vm", response_model=LeaseResponse)
async def lease_vm(request: LeaseRequest) -> LeaseResponse:
    """Lease VM capacity."""
    return _build_lease_response(request)


@app.post("/leases/gpu", response_model=LeaseResponse)
async def lease_gpu(request: LeaseRequest) -> LeaseResponse:
    """Lease GPU capacity."""
    return _build_lease_response(request)


@app.get("/premium/content")
async def get_premium_content(request: Request) -> FileResponse:
    """
    Temporary stub: treat any request that includes an X-Payment header
    as 'paid' and return the premium HTML asset.

    NOTE: This is NOT real payment verification; it's just a placeholder
    while wiring up the x402 client.
    """
    if not request.headers.get("X-Payment"):
        # Normally the x402 middleware will have already responded with 402
        # before the request reaches this handler. This extra check is just
        # a temporary guard while experimenting.
        raise HTTPException(status_code=402, detail="Payment required (temporary stub).")

    return FileResponse("static/premium.html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=4021)

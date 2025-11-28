from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

class LeaseRequest(BaseModel):
    sku: str
    runtimeMinutes: int
    hostname: Optional[str] = None
    cores: int = 1
    memoryMB: int = 512
    diskGB: int = 8
    password: str = Field(min_length=6, description="Default root password for the container")
    requester: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None

class LeaseResponse(BaseModel):
    leaseId: str
    status: str
    ctid: Optional[str] = None
    expiresAt: Optional[str] = None
    message: Optional[str] = None
    ownerWallet: Optional[str] = None

def build_lease_response(request: LeaseRequest) -> LeaseResponse:
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

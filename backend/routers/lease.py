from fastapi import APIRouter
from others.types import *

router = APIRouter(
    prefix="/lease",
    tags=["lease"],
)

@router.post("/container", response_model=LeaseResponse)
async def container(request: LeaseRequest) -> LeaseResponse:
    """lease container"""
    # do ops
    return build_lease_response(request)

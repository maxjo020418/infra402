from fastapi import (
    APIRouter, 
    Request,
)
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

router = APIRouter(
    prefix="/premium",
    tags=["test"],
)

@router.get("/content")
async def get_premium_content(request: Request) -> FileResponse:
    return FileResponse("static/premium.html")
from fastapi import APIRouter, Request
from pydantic import BaseModel

from .v1.router import router as router_v1

router = APIRouter()

router.include_router(
    router_v1,
    prefix="/v1",
    tags=[
        "v1",
    ],
)
router.include_router(
    router_v1,
    prefix="/latest",
    tags=[
        "latest",
    ],
)

LATEST_API_VERSION = "v1"


class ApiVersionInfo(BaseModel):
    latest: str


@router.get("", response_model=ApiVersionInfo)
def get_api_info(request: Request) -> ApiVersionInfo:
    return ApiVersionInfo(latest=LATEST_API_VERSION)

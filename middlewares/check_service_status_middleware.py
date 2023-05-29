from fastapi import Request
from fastapi.responses import JSONResponse

from internal.config import CHECK_SERVICE_STATUS
from internal.crud import StatusCollection
from internal.models import StatusModel


async def is_service_correctly_configured(request: Request, call_next):
    try:
        check_service_status_val = bool(int(CHECK_SERVICE_STATUS))
    except ValueError:
        check_service_status_val = True

    if not check_service_status_val:
        return await call_next(request)

    status = await StatusCollection.get_status()
    if not status:
        status = StatusModel(
            ok=False,
            error_msg="Cloud Environment (.json file) configuration was not processed by service before start",
        )
    if not status.ok:
        return JSONResponse(content=status.dict(), status_code=428)

    response = await call_next(request)
    return response

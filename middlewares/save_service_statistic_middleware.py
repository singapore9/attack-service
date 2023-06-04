import logging
import time

from fastapi import Request

from internal.config import CUSTOM_ENDPOINTS_STARTSWITH, SAVE_SERVICE_STATISTIC
from internal.crud import ResponseInfoCollection
from internal.logger import log_step_async
from internal.models import ResponseInfoModel

logger = logging.getLogger(__name__)


async def save_service_statistic(request: Request, call_next):
    if not any(
        request.url.path.startswith(prefix) for prefix in CUSTOM_ENDPOINTS_STARTSWITH
    ):
        return await call_next(request)

    try:
        save_service_statistic_val = bool(int(SAVE_SERVICE_STATISTIC))
    except ValueError:
        save_service_statistic_val = True

    if not save_service_statistic_val:
        return await call_next(request)

    start_time = time.time()
    response = await log_step_async(
        logger, f"call {request.url.path} and save it to statistics collection"
    )(call_next)(request)
    process_time = time.time() - start_time

    await ResponseInfoCollection.insert_one(
        ResponseInfoModel(
            id=str(start_time),
            duration=process_time,
            path=request.url.path,
            params=request.url.query or "",
        ).dict(by_alias=True)
    )

    return response

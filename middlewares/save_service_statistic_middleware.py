import time

from fastapi import Request

from internal.config import SAVE_SERVICE_STATISTIC
from internal.crud import ResponseInfoCollection
from internal.models import ResponseInfoModel


async def save_service_statistic(request: Request, call_next):
    try:
        save_service_statistic_val = bool(int(SAVE_SERVICE_STATISTIC))
    except ValueError:
        save_service_statistic_val = True

    if not save_service_statistic_val:
        return await call_next(request)

    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    await ResponseInfoCollection.insert_one(
        ResponseInfoModel(id=str(start_time), duration=process_time).dict(by_alias=True)
    )

    return response

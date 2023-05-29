from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from internal.config import ALLOWED_HOST, CHECK_SERVICE_STATUS
from internal.crud import StatusCollection
from internal.db import close_mongo_connection, connect_to_mongo
from internal.models import StatusModel
from routers.api import router as router_api

origins = []
origins.extend(ALLOWED_HOST)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router_api, prefix="/api", tags=["api"])


@app.middleware("http")
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


app.add_event_handler("startup", connect_to_mongo)
app.add_event_handler("shutdown", close_mongo_connection)


@app.get("/status", response_model=StatusModel)
async def get_status(request: Request) -> StatusModel:
    return await StatusCollection.get_status()

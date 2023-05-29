from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from internal.config import ALLOWED_HOST
from internal.crud import StatusCollection
from internal.db import close_mongo_connection, connect_to_mongo
from internal.models import StatusModel
from routers.api import router as router_api

from middlewares.check_service_status_middleware import (  # isort: skip
    is_service_correctly_configured,
)

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


is_service_correctly_configured = app.middleware("http")(
    is_service_correctly_configured
)


app.add_event_handler("startup", connect_to_mongo)
app.add_event_handler("shutdown", close_mongo_connection)


@app.get("/status", response_model=StatusModel)
async def get_status(request: Request) -> StatusModel:
    return await StatusCollection.get_status()

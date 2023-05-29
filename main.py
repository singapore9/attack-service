import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from internal.crud import StatusCollection
from internal.db import close_mongo_connection, connect_to_mongo
from internal.models import StatusModel
from routers.api import router as router_api

load_dotenv()

origins = []
origins.extend(os.getenv("ALLOWED_HOST", "localhost"))

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router_api, prefix="/api", tags=["api"])

app.add_event_handler("startup", connect_to_mongo)
app.add_event_handler("shutdown", close_mongo_connection)


@app.get("/status", response_model=StatusModel)
async def get_status(request: Request) -> StatusModel:
    status = await StatusCollection.get_status()
    if not status:
        status = StatusModel(
            ok=False,
            error_msg="Cloud Environment (.json file) configuration was not processed by service before start",
        )
    return status

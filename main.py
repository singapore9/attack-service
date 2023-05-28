import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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


class StatusModel(BaseModel):
    ok: bool = True


@app.get("/status", response_model=StatusModel)
def get_status(request: Request) -> StatusModel:
    return StatusModel()

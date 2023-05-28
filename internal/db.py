import os

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

MONGO_PORT = os.getenv("MONGODB_PORT_NUMBER")
MONGO_DB = os.getenv("MONGODB_DATABASE")

MONGODB_URL = f"mongodb://db:{MONGO_PORT}/{MONGO_DB}"


class DataBase:
    client: AsyncIOMotorClient = None


db = DataBase()


async def get_database() -> AsyncIOMotorClient:
    return db.client


async def connect_to_mongo():
    db.client = AsyncIOMotorClient(MONGODB_URL, maxPoolSize=10, minPoolSize=10)


async def close_mongo_connection():
    db.client.close()

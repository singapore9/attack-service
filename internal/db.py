from motor.motor_asyncio import AsyncIOMotorClient

from .config import MONGODB_URL


class DataBase:
    client: AsyncIOMotorClient = None


db = DataBase()


async def get_database() -> AsyncIOMotorClient:
    return db.client


async def connect_to_mongo():
    db.client = AsyncIOMotorClient(MONGODB_URL, maxPoolSize=10, minPoolSize=10)


async def close_mongo_connection():
    db.client.close()

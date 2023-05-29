from typing import Optional, Type, TypeVar

from .db import MONGO_DB, get_database
from .models import FirewallRule, VMInfo

Model = TypeVar("Model", bound="BaseModel")


class BaseCollection:
    @classmethod
    def name(cls):
        raise NotImplementedError

    @classmethod
    def get_model(cls) -> Type[Model]:
        raise NotImplementedError

    @classmethod
    async def get_collection(cls):
        db = (await get_database())[MONGO_DB]
        return db[cls.name()]

    @classmethod
    async def delete_many(cls, locator=None):
        locator = locator or {}
        collection = await cls.get_collection()
        return await collection.delete_many(locator)

    @classmethod
    async def insert_many(cls, documents):
        collection = await cls.get_collection()
        return await collection.insert_many(documents)

    @classmethod
    async def rewrite(cls, documents):
        await cls.delete_many()
        return await cls.insert_many(documents)

    @classmethod
    async def get_all(cls) -> list[Model]:
        collection = await cls.get_collection()
        cursor = await collection.find({})
        result = []
        for doc in cursor.to_list(length=None):
            doc["id"] = doc["_id"]
            del doc["_id"]
            result.append(cls.get_model().parse_obj(doc))
        return result

    @classmethod
    async def get_by_id(cls, id: str) -> Optional[Model]:
        collection = await cls.get_collection()
        cursor = await collection.find({"_id": id})
        result = []
        for doc in cursor.to_list(length=None):
            doc["id"] = doc["_id"]
            del doc["_id"]
            result.append(cls.get_model().parse_obj(doc))
        return result[0] if result else None


class VirtualMachineCollection(BaseCollection):
    @classmethod
    def name(cls):
        return "VirtualMachine"

    @classmethod
    def get_model(cls):
        return VMInfo


class FirewallRuleCollection(BaseCollection):
    @classmethod
    def name(cls):
        return "FirewallRule"

    @classmethod
    def get_model(cls):
        return FirewallRule

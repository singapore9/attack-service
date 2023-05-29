from typing import Type

from pydantic import BaseModel, parse_obj_as

from .db import MONGO_DB, get_database
from .models import FirewallRule, VMInfo


class BaseCollection:
    @classmethod
    def name(cls):
        raise NotImplementedError

    @classmethod
    def get_model(cls) -> Type[BaseModel]:
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
    async def get_all(cls):
        collection = await cls.get_collection()
        cursor = await collection.find({})
        result = []
        for doc in cursor.to_list(length=None):
            doc["id"] = doc["_id"]
            del doc["_id"]
            result.append(cls.get_model().parse_obj(doc))
        return result


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

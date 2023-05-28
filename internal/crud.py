from .db import MONGO_DB, get_database


class BaseCollection:
    @classmethod
    def name(cls):
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


class VirtualMachineCollection(BaseCollection):
    @classmethod
    def name(cls):
        return "VirtualMachine"


class FirewallRuleCollection(BaseCollection):
    @classmethod
    def name(cls):
        return "FirewallRule"

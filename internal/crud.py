import logging
from typing import AsyncIterable, Optional, Type, TypeVar

from .config import MONGO_DB
from .db import get_database
from .logger import log_step_async

from .models import (  # isort: skip
    FirewallRule,
    ResponseInfoModel,
    StatusModel,
    TagInfo,
    VMInfo,
)

Model = TypeVar("Model", bound="BaseModel")

logger = logging.getLogger(__name__)


class GetNamedCollectionMixin:
    @classmethod
    def name(cls):
        raise NotImplementedError

    @classmethod
    async def get_collection(cls):
        db = (await get_database())[MONGO_DB]
        return db[cls.name()]


class BaseCollection(GetNamedCollectionMixin):
    rename_id: bool = False

    @classmethod
    def rename(cls: Type[Model], doc: dict) -> dict:
        doc["id"] = doc["_id"]
        del doc["_id"]
        return doc

    @classmethod
    def get_model(cls) -> Type[Model]:
        raise NotImplementedError

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
    async def get_all(cls: Type[Model]) -> list[Model]:
        collection = await cls.get_collection()
        cursor = collection.find({})
        result = []
        for doc in await cursor.to_list(length=None):
            if cls.rename_id:
                doc = cls.rename(doc)
            result.append(cls.get_model().parse_obj(doc))
        return result

    @classmethod
    async def get_all_iter(cls) -> AsyncIterable[Model]:
        collection = await cls.get_collection()
        async for doc in collection.find({}):
            if cls.rename_id:
                doc = cls.rename(doc)
            obj = cls.get_model().parse_obj(doc)
            yield obj

    @classmethod
    async def get_by_id(cls, id: str) -> Optional[Model]:
        collection = await cls.get_collection()
        cursor = collection.find({"_id": id})
        result = []
        for doc in await cursor.to_list(length=None):
            if cls.rename_id:
                doc = cls.rename(doc)
            result.append(cls.get_model().parse_obj(doc))
        return result[0] if result else None


class VirtualMachineCollection(BaseCollection):
    rename_id: bool = True

    @classmethod
    def name(cls):
        return "VirtualMachine"

    @classmethod
    def get_model(cls):
        return VMInfo


class FirewallRuleCollection(BaseCollection):
    rename_id: bool = True

    @classmethod
    def name(cls):
        return "FirewallRule"

    @classmethod
    def get_model(cls):
        return FirewallRule


class TagInfoCollection(BaseCollection):
    @classmethod
    def name(cls):
        return "TagInfo"

    @classmethod
    def get_model(cls):
        return TagInfo

    @classmethod
    async def get_aggregated_tag_info(cls, tag: str) -> Optional[TagInfo]:
        collection = await cls.get_collection()
        cursor = collection.find({"tag": tag})

        has_tag_info = False
        tag_info = TagInfo(tag=tag, tagged_vm_ids=[], tags_with_access=[])
        for doc in await cursor.to_list(length=None):
            has_tag_info = True
            tag_info.tagged_vm_ids.extend(doc["tagged_vm_ids"])
            tag_info.tags_with_access.extend(doc["tags_with_access"])
        return tag_info if has_tag_info else None


class StatusCollection(BaseCollection):
    @classmethod
    def name(cls):
        return "ServiceStatus"

    @classmethod
    def get_model(cls) -> Type[StatusModel]:
        return StatusModel

    @classmethod
    async def rewrite(cls, status: StatusModel):
        collection = await cls.get_collection()
        await cls.delete_many()
        return await collection.insert_one(status.dict())

    @classmethod
    async def get_status(cls) -> Optional[StatusModel]:
        collection = await cls.get_collection()
        cursor = collection.find({})

        for doc in await cursor.to_list(length=None):
            return cls.get_model().parse_obj(doc)


class ResponseInfoCollection(BaseCollection):
    @classmethod
    def name(cls):
        return "ResponseInfo"

    @classmethod
    def get_model(cls) -> Type[ResponseInfoModel]:
        return ResponseInfoModel

    @classmethod
    @log_step_async(logger, "insert request data to DB")
    async def insert_one(cls, document):
        collection = await cls.get_collection()
        return await collection.insert_one(document)

    @classmethod
    async def get_average_duration(cls):
        collection = await cls.get_collection()
        pipeline = [{"$group": {"_id": None, "avg_val": {"$avg": "$duration"}}}]
        async for info in collection.aggregate(pipeline):
            return info["avg_val"]

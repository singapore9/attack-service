from typing import Any, AsyncIterable, Optional, Type, TypeVar

from .config import MONGO_DB
from .db import get_database

from .models import (  # isort: skip
    FirewallRule,
    ResponseInfoModel,
    StatusModel,
    TagInfo,
    VMInfo,
)

Model = TypeVar("Model", bound="BaseModel")


class GetNamedCollectionMixin:
    @classmethod
    def name(cls):
        raise NotImplementedError

    @classmethod
    async def get_collection(cls):
        db = (await get_database())[MONGO_DB]
        return db[cls.name()]


class BaseCollection(GetNamedCollectionMixin):
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
    async def get_all(cls) -> list[Model]:
        collection = await cls.get_collection()
        cursor = collection.find({})
        result = []
        for doc in await cursor.to_list(length=None):
            doc["id"] = doc["_id"]
            del doc["_id"]
            result.append(cls.get_model().parse_obj(doc))
        return result

    @classmethod
    async def get_all_iter(cls) -> AsyncIterable[Model]:
        collection = await cls.get_collection()
        async for doc in collection.find({}):
            doc["id"] = doc["_id"]
            del doc["_id"]
            obj = cls.get_model().parse_obj(doc)
            yield obj

    @classmethod
    async def get_by_id(cls, id: str) -> Optional[Model]:
        collection = await cls.get_collection()
        cursor = collection.find({"_id": id})
        result = []
        for doc in await cursor.to_list(length=None):
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


class TagInfoCollection(BaseCollection):
    @classmethod
    def name(cls):
        return "TagInfo"

    @classmethod
    def get_model(cls):
        return TagInfo

    @classmethod
    async def _add_item_into_list_field_for_tag(
        cls, tag: str, field_name: str, item: Any
    ):
        tag_info: Optional[TagInfo] = await cls.get_by_id(tag)
        if tag_info:
            field_value: list[Any] = getattr(tag_info, field_name)
            if item not in field_value:
                field_value.append(item)
                setattr(tag_info, field_name, field_value)
                collection = await cls.get_collection()
                await collection.find_one_and_replace({"_id": tag}, tag_info.to_db())
        else:
            tag_info = TagInfo(id=tag, tagged_vm_ids=[], destination_tags=[])
            setattr(
                tag_info,
                field_name,
                [
                    item,
                ],
            )
            collection = await cls.get_collection()
            await collection.insert_one(tag_info.to_db())

    @classmethod
    async def add_vm_for_tag(cls, tag: str, vm_id: str):
        await cls._add_item_into_list_field_for_tag(tag, "tagged_vm_ids", vm_id)

    @classmethod
    async def add_destination_tag_for_tag(cls, tag: str, destination_tag: str):
        await cls._add_item_into_list_field_for_tag(
            tag, "destination_tags", destination_tag
        )


class StatusCollection(GetNamedCollectionMixin):
    @classmethod
    def name(cls):
        return "ServiceStatus"

    @classmethod
    def get_model(cls) -> Type[StatusModel]:
        return StatusModel

    @classmethod
    async def delete_many(cls, locator=None):
        locator = locator or {}
        collection = await cls.get_collection()
        return await collection.delete_many(locator)

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


class ResponseInfoCollection(GetNamedCollectionMixin):
    @classmethod
    def name(cls):
        return "ResponseInfo"

    @classmethod
    def get_model(cls) -> Type[ResponseInfoModel]:
        return ResponseInfoModel

    @classmethod
    async def delete_many(cls, locator=None):
        locator = locator or {}
        collection = await cls.get_collection()
        return await collection.delete_many(locator)

    @classmethod
    async def insert_one(cls, document):
        collection = await cls.get_collection()
        return await collection.insert_one(document)

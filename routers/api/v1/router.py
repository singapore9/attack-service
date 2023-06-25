from asyncio import gather
from typing import Type

from fastapi import APIRouter, Request
from pydantic import BaseModel

from internal.processor import get_vm_id_list_with_access_to_vm

from internal.crud import (  # isort: skip
    GetNamedCollectionMixin,
    ResponseInfoCollection,
    VirtualMachineCollection,
)

router = APIRouter()


VmId = str
VmIdsList = list[VmId]


@router.get("/attack", response_model=VmIdsList)
async def do_attack(request: Request, vm_id: VmId) -> VmIdsList:
    return await get_vm_id_list_with_access_to_vm(vm_id)


class ServiceStatisticInfo(BaseModel):
    vm_count: int
    request_count: int
    average_request_time: float


async def get_docs_count(collection: Type[GetNamedCollectionMixin]):
    collection = await collection.get_collection()
    doc_count = await collection.count_documents({})
    return doc_count


@router.get("/stat", response_model=ServiceStatisticInfo)
async def get_statistic(request: Request) -> ServiceStatisticInfo:
    vm_count, resp_count, average_time = await gather(
        get_docs_count(VirtualMachineCollection),
        get_docs_count(ResponseInfoCollection),
        ResponseInfoCollection.get_average_duration(),
    )

    return ServiceStatisticInfo(
        vm_count=vm_count,
        request_count=resp_count,
        average_request_time=average_time or 0,
    )

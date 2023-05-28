from fastapi import APIRouter, Request

from internal.processor import get_affected_vm_id_list

router = APIRouter()


VmId = str
VmIdsList = list[VmId]


@router.get("/attack", response_model=VmIdsList)
async def do_attack(request: Request, vm_id: VmId) -> VmIdsList:
    return await get_affected_vm_id_list(vm_id)

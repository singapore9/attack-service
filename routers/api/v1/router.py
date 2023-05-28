from fastapi import APIRouter, Request

router = APIRouter()


VmId = str
VmIdsList = list[VmId]


@router.get("/attack", response_model=VmIdsList)
async def do_attack(request: Request, vm_id: VmId) -> VmIdsList:
    return []

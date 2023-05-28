from .extractor import get_cloud_environment


async def get_affected_vm_id_list(vm_id: str) -> list[str]:
    cloud_environment = await get_cloud_environment()
    return [vm_id]

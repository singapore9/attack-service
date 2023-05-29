from asyncio import gather
from itertools import chain
from typing import Optional

from .crud import TagInfoCollection, VirtualMachineCollection
from .models import TagInfo, VMInfo


async def get_affected_vm_ids_by_tag(
    tag: str,
) -> list[str]:
    tag_info: Optional[TagInfo] = await TagInfoCollection.get_by_id(tag)
    if not tag_info:
        return []

    total_affected_vm_ids_by_tag = []
    affected_dest_tags = tag_info.destination_tags

    for affected_tag in affected_dest_tags:
        affected_tag_info: Optional[TagInfo] = await TagInfoCollection.get_by_id(
            affected_tag
        )
        if affected_tag_info:
            total_affected_vm_ids_by_tag.extend(affected_tag_info.tagged_vm_ids)
    return total_affected_vm_ids_by_tag


async def get_affected_vm_id_list(vm_id: str) -> list[str]:
    first_vm: Optional[VMInfo] = await VirtualMachineCollection.get_by_id(vm_id)
    accessed_tags = first_vm.tags if first_vm else []

    if not accessed_tags:
        return []

    gather_results = await gather(
        *[get_affected_vm_ids_by_tag(tag) for tag in accessed_tags]
    )

    total_affected_vm_ids = set(chain.from_iterable(gather_results))

    if vm_id in total_affected_vm_ids:
        total_affected_vm_ids.remove(vm_id)

    return list(total_affected_vm_ids)

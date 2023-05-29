import logging
from asyncio import gather
from itertools import chain
from typing import Optional

from .crud import TagInfoCollection, VirtualMachineCollection
from .models import TagInfo, VMInfo

logger = logging.getLogger("asyncio")
logger.setLevel(logging.DEBUG)


async def get_affected_vm_ids_by_tag(
    tag: str,
) -> list[str]:
    tag_info: Optional[TagInfo] = await TagInfoCollection.get_by_id(tag)
    if not tag_info:
        print(f"No affected tags by {tag}")
        return []

    total_affected_vm_ids_by_tag = []
    affected_dest_tags = tag_info.destination_tags

    print(f"Affected tags by {tag}: {affected_dest_tags}")

    for affected_tag in affected_dest_tags:
        affected_tag_info: Optional[TagInfo] = await TagInfoCollection.get_by_id(
            affected_tag
        )
        if affected_tag_info:
            total_affected_vm_ids_by_tag.extend(affected_tag_info.tagged_vm_ids)
    print(f"Affected VMs by {tag}: {total_affected_vm_ids_by_tag}")
    return total_affected_vm_ids_by_tag


async def get_affected_vm_id_list(vm_id: str) -> list[str]:
    first_vm: Optional[VMInfo] = await VirtualMachineCollection.get_by_id(vm_id)
    accessed_tags = first_vm.tags if first_vm else []

    print(f"VirtualMachine {vm_id} has tags: {accessed_tags}")
    if not accessed_tags:
        return []

    gather_results = await gather(
        *[get_affected_vm_ids_by_tag(tag) for tag in accessed_tags]
    )

    total_affected_vm_ids = set(chain.from_iterable(gather_results))
    print(f"Total affected VMs: {total_affected_vm_ids}")

    if vm_id in total_affected_vm_ids:
        print(f"Exclude {vm_id}")
        total_affected_vm_ids.remove(vm_id)

    return list(total_affected_vm_ids)

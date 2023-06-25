import logging
from asyncio import gather
from itertools import chain
from typing import Optional

from .crud import TagInfoCollection, VirtualMachineCollection
from .logger import log_step_async
from .models import TagInfo, VMInfo

asyncio_logger = logging.getLogger("asyncio")
asyncio_logger.setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)


@log_step_async(logger, "calculating VMs with access to specified tag")
async def get_vm_ids_with_access_to_tag(
    tag: str,
) -> list[str]:
    tag_info: Optional[TagInfo] = await TagInfoCollection.get_aggregated_tag_info(tag)
    if not tag_info:
        logger.debug(f"No tags with access to {tag}")
        return []

    total_vm_ids_with_access_to_tag = []
    tags_with_access = tag_info.tags_with_access

    logger.debug(f"Tags with access to {tag}: {tags_with_access}")

    for tag_with_access in tags_with_access:
        tag_with_access_info: Optional[
            TagInfo
        ] = await TagInfoCollection.get_aggregated_tag_info(tag_with_access)
        if tag_with_access_info:
            total_vm_ids_with_access_to_tag.extend(tag_with_access_info.tagged_vm_ids)
    logger.debug(
        f"VMs who can attack specified TAG - {len(total_vm_ids_with_access_to_tag)}: "
        "{total_vm_ids_with_access_to_tag[:4]}..."
    )
    return total_vm_ids_with_access_to_tag


@log_step_async(logger, "calculating VMs with access to specified VM")
async def get_vm_id_list_with_access_to_vm(vm_id: str) -> list[str]:
    first_vm: Optional[VMInfo] = await VirtualMachineCollection.get_by_id(vm_id)
    tags_in_danger = first_vm.tags if first_vm else []

    logger.debug(f"VirtualMachine {vm_id} has tags: {tags_in_danger}")
    if not tags_in_danger:
        return []

    gather_results = await gather(
        *[get_vm_ids_with_access_to_tag(tag) for tag in tags_in_danger]
    )

    total_vm_id_list_with_access_to_vm = set(chain.from_iterable(gather_results))
    logger.debug(
        f"VMs who can attack specified VM - {len(total_vm_id_list_with_access_to_vm)}"
    )

    if vm_id in total_vm_id_list_with_access_to_vm:
        logger.debug(f"Exclude {vm_id}")
        total_vm_id_list_with_access_to_vm.remove(vm_id)

    return list(total_vm_id_list_with_access_to_vm)

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


@log_step_async(
    logger, "calculating VMs which are available from FW rules for specified tag"
)
async def get_affected_vm_ids_by_tag(
    tag: str,
) -> list[str]:
    tag_info: Optional[TagInfo] = await TagInfoCollection.get_aggregated_tag_info(tag)
    if not tag_info:
        logger.debug(f"No affected tags by {tag}")
        return []

    total_affected_vm_ids_by_tag = []
    affected_dest_tags = tag_info.destination_tags

    logger.debug(f"Affected tags by {tag}: {affected_dest_tags}")

    for affected_tag in affected_dest_tags:
        affected_tag_info: Optional[
            TagInfo
        ] = await TagInfoCollection.get_aggregated_tag_info(affected_tag)
        if affected_tag_info:
            total_affected_vm_ids_by_tag.extend(affected_tag_info.tagged_vm_ids)
    logger.debug(
        f"Affected VMs - {len(total_affected_vm_ids_by_tag)}: {total_affected_vm_ids_by_tag[:4]}..."
    )
    return total_affected_vm_ids_by_tag


@log_step_async(logger, "calculating VMs which are available from specified VM")
async def get_affected_vm_id_list(vm_id: str) -> list[str]:
    first_vm: Optional[VMInfo] = await VirtualMachineCollection.get_by_id(vm_id)
    accessed_tags = first_vm.tags if first_vm else []

    logger.debug(f"VirtualMachine {vm_id} has tags: {accessed_tags}")
    if not accessed_tags:
        return []

    gather_results = await gather(
        *[get_affected_vm_ids_by_tag(tag) for tag in accessed_tags]
    )

    total_affected_vm_ids = set(chain.from_iterable(gather_results))
    logger.debug(f"Total affected VMs - {len(total_affected_vm_ids)}")

    if vm_id in total_affected_vm_ids:
        logger.debug(f"Exclude {vm_id}")
        total_affected_vm_ids.remove(vm_id)

    return list(total_affected_vm_ids)

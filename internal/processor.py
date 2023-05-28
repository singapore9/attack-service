from asyncio import gather
from collections import defaultdict
from itertools import chain

from .extractor import get_cloud_environment


async def get_affected_vm_ids_by_tag(
    vm_ids_by_tag: dict[str, list[str]],
    dest_tags_by_source_tag: dict[str, set[str]],
    tag: str,
) -> list[str]:
    total_affected_vm_ids_by_tag = []
    affected_dest_tags = dest_tags_by_source_tag.get(tag, set())
    for affected_tag in affected_dest_tags:
        affected_vm_ids = vm_ids_by_tag.get(affected_tag, [])
        total_affected_vm_ids_by_tag.extend(affected_vm_ids)
    return total_affected_vm_ids_by_tag


async def get_affected_vm_id_list(vm_id: str) -> list[str]:
    cloud_environment = await get_cloud_environment()
    vm_ids_by_tag = defaultdict(list)

    can_use_tags = []
    for vm in cloud_environment.machines:
        if vm.id == vm_id:
            can_use_tags = vm.tags

        for tag in vm.tags:
            vm_ids_by_tag[tag].append(vm.id)
    dest_tags_by_source_tag = defaultdict(set)
    for fw_rule in cloud_environment.rules:
        dest_tags_by_source_tag[fw_rule.source_tag].add(fw_rule.dest_tag)

    gather_results = await gather(
        *[
            get_affected_vm_ids_by_tag(vm_ids_by_tag, dest_tags_by_source_tag, tag)
            for tag in can_use_tags
        ]
    )

    total_affected_vm_ids = set(chain.from_iterable(gather_results))

    if vm_id in total_affected_vm_ids:
        total_affected_vm_ids.remove(vm_id)

    return list(total_affected_vm_ids)

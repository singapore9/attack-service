import logging
from asyncio import gather, get_event_loop
from collections import defaultdict
from datetime import datetime

from pydantic import ValidationError

from .db import connect_to_mongo
from .extractor import get_cloud_environment
from .logger import configure_logger, get_logger_filename, log_step_async
from .models import FirewallRule, StatusModel, TagInfo

from .crud import (  # isort: skip
    FirewallRuleCollection,
    StatusCollection,
    TagInfoCollection,
    VirtualMachineCollection,
    ResponseInfoCollection,
)


logger = logging.getLogger(__name__)

MONGO_ARRAY_ELEMS_COUNT = (
    100000  # For preventing having huge BSON. It leads to Mongo errors
)


def chunks(items, size):
    for i in range(0, len(items), size):
        yield items[i : i + size]


@log_step_async(logger, "calculate VM IDs for tag")
async def calculate_vm_ids_for_tags():
    vm_ids_for_tag = defaultdict(list)
    async for vm in VirtualMachineCollection.get_all_iter():
        vm_id = vm.id
        for tag in vm.tags:
            vm_ids_for_tag[tag].append(vm_id)
    return vm_ids_for_tag


@log_step_async(logger, "insert VMs for one tag")
async def insert_data_about_one_tag_vms(tag, vm_ids):
    collection = await TagInfoCollection.get_collection()

    await gather(
        *[
            collection.insert_one(
                TagInfo(tag=tag, tagged_vm_ids=vm_ids_chunk, tags_with_access=[]).dict()
            )
            for vm_ids_chunk in chunks(vm_ids, MONGO_ARRAY_ELEMS_COUNT)
        ]
    )
    return


@log_step_async(logger, "insert VMs for all tags")
async def add_vms_for_tags():
    vm_ids_for_tag = await calculate_vm_ids_for_tags()
    await gather(
        *[
            insert_data_about_one_tag_vms(tag, vm_ids)
            for tag, vm_ids in vm_ids_for_tag.items()
        ]
    )
    del vm_ids_for_tag
    return


@log_step_async(logger, "calculate Tags With Access for tag")
async def calculate_tags_with_access_for_tags():
    tags_with_access_for_tag = defaultdict(set)
    async for rule in FirewallRuleCollection.get_all_iter():
        tags_with_access_for_tag[rule.dest_tag].add(rule.source_tag)
    return tags_with_access_for_tag


@log_step_async(logger, "insert Tags With Access for one tag")
async def insert_data_about_one_tag_tags_with_access(tag, tags_with_access):
    collection = await TagInfoCollection.get_collection()
    await gather(
        *[
            collection.insert_one(
                TagInfo(
                    tag=tag, tagged_vm_ids=[], tags_with_access=tags_with_access_chunk
                ).dict()
            )
            for tags_with_access_chunk in chunks(
                list(tags_with_access), MONGO_ARRAY_ELEMS_COUNT
            )
        ]
    )
    return


@log_step_async(logger, "insert Tags With Access for all tags")
async def add_tags_with_access_for_tags():
    tags_with_access_for_tag = await calculate_tags_with_access_for_tags()
    await gather(
        *[
            insert_data_about_one_tag_tags_with_access(tag, tags_with_access)
            for tag, tags_with_access in tags_with_access_for_tag.items()
        ]
    )
    del tags_with_access_for_tag
    return


@log_step_async(logger, "preparing server")
async def prepare_server():
    await connect_to_mongo()

    await StatusCollection.rewrite(
        StatusModel(
            ok=False,
            error_msg=(
                f"Cloud Environment config reading is in progress. "
                f"It was started at {datetime.utcnow()}"
            ),
        )
    )

    error_msg = None
    try:
        cloud_environment = await get_cloud_environment()
    except ValidationError as e:
        msg = "Cloud Environment was not specified correctly"
        logger.exception(msg)
        error_msg = f"{msg}:\n{e}"
    except Exception as e:
        msg = "Unspecified error before server was started"
        logger.exception(msg)
        error_msg = f"{msg}:\n{e}"

    if error_msg:
        await StatusCollection.rewrite(StatusModel(ok=False, error_msg=error_msg))
        return

    filtered_rules: set[tuple] = {
        (rule.source_tag, rule.dest_tag) for rule in cloud_environment.rules
    }

    await gather(
        VirtualMachineCollection.rewrite(
            [obj.to_db() for obj in cloud_environment.machines]
        ),
        FirewallRuleCollection.rewrite(
            [
                FirewallRule(
                    id=str(f"fw-{i}"), source_tag=rule_info[0], dest_tag=rule_info[1]
                ).to_db()
                for i, rule_info in enumerate(filtered_rules)
            ]
        ),
        TagInfoCollection.delete_many(),
        StatusCollection.delete_many(),
        ResponseInfoCollection.delete_many(),
    )

    await add_vms_for_tags()
    await add_tags_with_access_for_tags()

    await StatusCollection.rewrite(StatusModel(ok=True, error_msg=""))


if __name__ == "__main__":
    logs_filename = get_logger_filename(__file__)
    configure_logger(logs_filename, logging.DEBUG)

    loop = get_event_loop()
    loop.run_until_complete(prepare_server())

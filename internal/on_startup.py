from asyncio import gather, get_event_loop

from pydantic import ValidationError

from .db import connect_to_mongo
from .extractor import get_cloud_environment
from .models import FirewallRule, StatusModel

from .crud import (  # isort: skip
    FirewallRuleCollection,
    StatusCollection,
    TagInfoCollection,
    VirtualMachineCollection,
    ResponseInfoCollection,
)


async def prepare_server():
    await connect_to_mongo()
    error_msg = None
    try:
        cloud_environment = await get_cloud_environment()
    except ValidationError as e:
        error_msg = f"Cloud Environment was not specified correctly:\n{e}"
    except Exception as e:
        error_msg = f"Unspecified error before server was started:\n{e}"

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

    async for vm in VirtualMachineCollection.get_all_iter():
        vm_id = vm.id
        if vm.tags:
            await gather(
                *[TagInfoCollection.add_vm_for_tag(tag, vm_id) for tag in vm.tags]
            )

    fw_rule_coros = []
    async for fw_rule in FirewallRuleCollection.get_all_iter():
        fw_rule_coros.append(
            TagInfoCollection.add_destination_tag_for_tag(
                fw_rule.source_tag, fw_rule.dest_tag
            )
        )
    if fw_rule_coros:
        await gather(*fw_rule_coros)
    await StatusCollection.rewrite(StatusModel(ok=True, error_msg=""))


if __name__ == "__main__":
    loop = get_event_loop()
    loop.run_until_complete(prepare_server())

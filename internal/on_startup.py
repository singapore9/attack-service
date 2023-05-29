from asyncio import gather, get_event_loop

from .db import connect_to_mongo
from .extractor import get_cloud_environment
from .models import FirewallRule

from .crud import (  # isort: skip
    FirewallRuleCollection,
    TagInfoCollection,
    VirtualMachineCollection,
)


async def prepare_server():
    await connect_to_mongo()
    cloud_environment = await get_cloud_environment()
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
    )

    async for vm in VirtualMachineCollection.get_all_iter():
        vm_id = vm.id
        await gather(*[TagInfoCollection.add_vm_for_tag(tag, vm_id) for tag in vm.tags])

    fw_rule_coros = []
    async for fw_rule in FirewallRuleCollection.get_all_iter():
        fw_rule_coros.append(
            TagInfoCollection.add_destination_tag_for_tag(
                fw_rule.source_tag, fw_rule.dest_tag
            )
        )
    await gather(*fw_rule_coros)


if __name__ == "__main__":
    loop = get_event_loop()
    loop.run_until_complete(prepare_server())

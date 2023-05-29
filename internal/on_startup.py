from asyncio import gather, get_event_loop

from .crud import FirewallRuleCollection, VirtualMachineCollection
from .db import connect_to_mongo
from .extractor import get_cloud_environment
from .models import FirewallRule


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
    )


if __name__ == "__main__":
    loop = get_event_loop()
    loop.run_until_complete(prepare_server())

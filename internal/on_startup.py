from asyncio import gather, get_event_loop

from .crud import FirewallRuleCollection, VirtualMachineCollection
from .db import connect_to_mongo
from .extractor import get_cloud_environment


async def prepare_server():
    await connect_to_mongo()
    cloud_environment = await get_cloud_environment()

    await gather(
        VirtualMachineCollection.rewrite(
            [obj.to_db() for obj in cloud_environment.machines]
        ),
        FirewallRuleCollection.rewrite(
            [obj.to_db() for obj in cloud_environment.rules]
        ),
    )


if __name__ == "__main__":
    loop = get_event_loop()
    loop.run_until_complete(prepare_server())

from unittest import IsolatedAsyncioTestCase, mock, skip

from .models import CloudEnvironment, FirewallRule, VMInfo
from .processor import get_affected_vm_id_list


class AttachTestCase(IsolatedAsyncioTestCase):
    @skip(reason="Processor hasn't have correct logic yet")
    async def test_processor_positive(self):
        with mock.patch(
            "internal.processor.get_cloud_environment"
        ) as get_cloud_environment_mock:
            get_cloud_environment_mock.return_value = CloudEnvironment(
                machines=[
                    VMInfo(id="id1", name="n1", tags=["t1"]),
                    VMInfo(id="id2", name="n2", tags=["t2"]),
                ],
                rules=[FirewallRule(id="id1", source_tag="t2", dest_tag="t1")],
            )
            result = await get_affected_vm_id_list("id2")

        self.assertEqual(
            result,
            ["id1"],
            "One rule links two VMs. When destination is mentioned, the second VM should be returned",
        )

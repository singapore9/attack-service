from time import time
from unittest import IsolatedAsyncioTestCase, mock, skip

from .models import CloudEnvironment, FirewallRule, VMInfo
from .processor import get_affected_vm_id_list


class ProcessorTestCase(IsolatedAsyncioTestCase):
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

    @skip(reason="Cloud Environment processor's code has not been optimized yet")
    async def test_processor_huge_data(self):
        VM_COUNT = 100000
        FW_RULES_COUNT = 100000
        TAGS_VARIATION = 100

        EXPECTED_EXECUTION_TIME_SEC = 2

        with mock.patch(
            "internal.processor.get_cloud_environment"
        ) as get_cloud_environment_mock:
            get_cloud_environment_mock.return_value = CloudEnvironment(
                machines=[
                    VMInfo(
                        id=f"id{i}",
                        name=f"n{i}",
                        tags=[
                            f"t{j}"
                            for j in range(
                                max(i - TAGS_VARIATION, 0), i + TAGS_VARIATION
                            )
                        ],
                    )
                    for i in range(VM_COUNT)
                ],
                rules=[
                    FirewallRule(id=f"fw_id{i}", source_tag=f"t{i}", dest_tag=f"t{i-1}")
                    for i in range(FW_RULES_COUNT)
                ],
            )
            before = time()
            await get_affected_vm_id_list("id2")
            after = time()
        self.assertGreater(
            EXPECTED_EXECUTION_TIME_SEC,
            before - after,
            "Huge list of VMs and FW rules requires want be handled quickly too",
        )

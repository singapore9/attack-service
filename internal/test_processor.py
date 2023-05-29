from time import time
from unittest import IsolatedAsyncioTestCase, mock, skip

from parameterized import parameterized

from .models import FirewallRule, VMInfo
from .processor import get_affected_vm_id_list


def get_mock_path(item: str) -> str:
    return f"internal.processor.{item}"


class ProcessorTestCase(IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.longMessage = True

    async def test_processor_positive(self):
        with mock.patch(
            get_mock_path("FirewallRuleCollection")
        ) as fw_rule_collection_mock:
            fw_rule_collection_mock.get_all = mock.AsyncMock(
                return_value=[FirewallRule(id="id1", source_tag="t2", dest_tag="t1")]
            )
            with mock.patch(
                get_mock_path("VirtualMachineCollection")
            ) as vm_collection_mock:
                vm_dict = {
                    "id1": VMInfo(id="id1", name="n1", tags=["t1"]),
                    "id2": VMInfo(id="id2", name="n2", tags=["t2"]),
                }
                vm_collection_mock.get_all = mock.AsyncMock(
                    return_value=list(vm_dict.values())
                )
                vm_collection_mock.get_by_id = mock.AsyncMock(
                    side_effect=lambda id: vm_dict.get(id)
                )
                result = await get_affected_vm_id_list("id2")

        self.assertEqual(
            result,
            ["id1"],
            "One rule links two VMs. When destination is mentioned, the second VM should be returned",
        )

    @parameterized.expand(
        (
            (
                "Simple test",
                "vm-1",
                {
                    "vm-2",
                },
            ),
            (
                "Few Firewall rules have the same tags (IDs are different)",
                "vm-2",
                {
                    "vm-3",
                },
            ),
            ("Attacked VM has few tags", "vm-4", {"vm-5", "vm-6"}),
            (
                "Attacked VM has tag which is in danger. We don't need to show attacked VM",
                "vm-7",
                {"vm-8"},
            ),
            ("VM ID is incorrect. No VMs are in danger", "unknown_vm_id", set()),
        )
    )
    async def test_processor_with_different_vms(self, reason, vm_id, expected_vm_ids):
        with mock.patch(
            get_mock_path("FirewallRuleCollection")
        ) as fw_rule_collection_mock:
            fw_rule_collection_mock.get_all = mock.AsyncMock(
                return_value=[
                    FirewallRule.parse_obj(obj)
                    for obj in [
                        {
                            "fw_id": "fw-1_0",
                            "source_tag": "tag-1_0",
                            "dest_tag": "tag-1_1",
                        },
                        {
                            "fw_id": "fw-2_0",
                            "source_tag": "tag-2_0",
                            "dest_tag": "tag-2_1",
                        },
                        {
                            "fw_id": "fw-2_1",
                            "source_tag": "tag-2_0",
                            "dest_tag": "tag-2_1",
                        },
                        {
                            "fw_id": "fw-3_0",
                            "source_tag": "tag-3_0",
                            "dest_tag": "tag-3_2",
                        },
                        {
                            "fw_id": "fw-3_1",
                            "source_tag": "tag-3_1",
                            "dest_tag": "tag-3_3",
                        },
                        {
                            "fw_id": "fw-4_0",
                            "source_tag": "tag-4_0",
                            "dest_tag": "tag-4_1",
                        },
                    ]
                ]
            )
            with mock.patch(
                get_mock_path("VirtualMachineCollection")
            ) as vm_collection_mock:
                vm_dict = {
                    obj["vm_id"]: VMInfo.parse_obj(obj)
                    for obj in [
                        {"vm_id": "vm-1", "name": "", "tags": ["tag-1_0"]},
                        {
                            "vm_id": "vm-2",
                            "name": "",
                            "tags": ["tag-1_1", "tag-2_0"],
                        },
                        {"vm_id": "vm-3", "name": "", "tags": ["tag-2_1"]},
                        {
                            "vm_id": "vm-4",
                            "name": "",
                            "tags": ["tag-3_0", "tag-3_1"],
                        },
                        {"vm_id": "vm-5", "name": "", "tags": ["tag-3_2"]},
                        {"vm_id": "vm-6", "name": "", "tags": ["tag-3_3"]},
                        {
                            "vm_id": "vm-7",
                            "name": "",
                            "tags": ["tag-4_0", "tag-4_1"],
                        },
                        {"vm_id": "vm-8", "name": "", "tags": ["tag-4_1"]},
                    ]
                }
                vm_collection_mock.get_all = mock.AsyncMock(
                    return_value=list(vm_dict.values())
                )
                vm_collection_mock.get_by_id = mock.AsyncMock(
                    side_effect=lambda id: vm_dict.get(id)
                )
                result = await get_affected_vm_id_list(vm_id)

        self.assertEqual(
            set(result),
            expected_vm_ids,
            reason,
        )

    @skip(reason="Cloud Environment processor's code has not been optimized yet")
    async def test_processor_huge_data(self):
        VM_COUNT = 100000
        FW_RULES_COUNT = 100000
        TAGS_VARIATION = 100

        EXPECTED_EXECUTION_TIME_SEC = 2

        with mock.patch(
            get_mock_path("FirewallRuleCollection")
        ) as fw_rule_collection_mock:
            fw_rule_collection_mock.get_all = mock.AsyncMock(
                return_value=[
                    FirewallRule(id=f"fw_id{i}", source_tag=f"t{i}", dest_tag=f"t{i-1}")
                    for i in range(FW_RULES_COUNT)
                ]
            )

            with mock.patch(
                get_mock_path("VirtualMachineCollection")
            ) as vm_collection_mock:
                vm_dict = {
                    f"id{i}": VMInfo(
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
                }
                vm_collection_mock.get_all = mock.AsyncMock(
                    return_value=list(vm_dict.values())
                )
                vm_collection_mock.get_by_id = mock.AsyncMock(
                    side_effect=lambda id: vm_dict.get(id)
                )

            before = time()
            await get_affected_vm_id_list("id2")
            after = time()
        self.assertGreater(
            EXPECTED_EXECUTION_TIME_SEC,
            before - after,
            "Huge list of VMs and FW rules requires want be handled quickly too",
        )

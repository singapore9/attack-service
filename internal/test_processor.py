from unittest import IsolatedAsyncioTestCase, mock

from parameterized import parameterized

from .models import TagInfo, VMInfo
from .processor import get_affected_vm_id_list


def get_mock_path(item: str) -> str:
    return f"internal.processor.{item}"


class ProcessorTestCase(IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.longMessage = True

    async def test_processor_positive(self):
        with mock.patch(get_mock_path("TagInfoCollection")) as tag_info_collection_mock:
            tag_info_dict = {
                "t1": TagInfo(tag="t1", destination_tags=[], tagged_vm_ids=["id1"]),
                "t2": TagInfo(
                    tag="t2",
                    destination_tags=[
                        "t1",
                    ],
                    tagged_vm_ids=["id2"],
                ),
            }
            tag_info_collection_mock.get_aggregated_tag_info = mock.AsyncMock(
                side_effect=lambda id: tag_info_dict.get(id)
            )
            with mock.patch(
                get_mock_path("VirtualMachineCollection")
            ) as vm_collection_mock:
                vm_dict = {
                    "id1": VMInfo(id="id1", name="n1", tags=["t1"]),
                    "id2": VMInfo(id="id2", name="n2", tags=["t2"]),
                }
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
        with mock.patch(get_mock_path("TagInfoCollection")) as tag_info_collection_mock:
            tag_info_dict = {
                "tag-1_0": TagInfo(
                    tag="tag-1_0", destination_tags=["tag-1_1"], tagged_vm_ids=["vm-1"]
                ),
                "tag-1_1": TagInfo(
                    tag="tag-1_1", destination_tags=[], tagged_vm_ids=["vm-2"]
                ),
                "tag-2_0": TagInfo(
                    tag="tag-2_0", destination_tags=["tag-2_1"], tagged_vm_ids=["vm-2"]
                ),
                "tag-2_1": TagInfo(
                    tag="tag-2_1", destination_tags=[], tagged_vm_ids=["vm-3"]
                ),
                "tag-3_0": TagInfo(
                    tag="tag-3_0", destination_tags=["tag-3_2"], tagged_vm_ids=["vm-4"]
                ),
                "tag-3_1": TagInfo(
                    tag="tag-3_1", destination_tags=["tag-3_3"], tagged_vm_ids=["vm-4"]
                ),
                "tag-3_2": TagInfo(
                    tag="tag-3_2", destination_tags=[], tagged_vm_ids=["vm-5"]
                ),
                "tag-3_3": TagInfo(
                    tag="tag-3_3", destination_tags=[], tagged_vm_ids=["vm-6"]
                ),
                "tag-4_0": TagInfo(
                    tag="tag-4_0", destination_tags=["tag-4_1"], tagged_vm_ids=["vm-7"]
                ),
                "tag-4_1": TagInfo(
                    tag="tag-4_1", destination_tags=[], tagged_vm_ids=["vm-7", "vm-8"]
                ),
            }
            tag_info_collection_mock.get_aggregated_tag_info = mock.AsyncMock(
                side_effect=lambda id: tag_info_dict.get(id)
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
                        {
                            "vm_id": "vm-4",
                            "name": "",
                            "tags": ["tag-3_0", "tag-3_1"],
                        },
                        {
                            "vm_id": "vm-7",
                            "name": "",
                            "tags": ["tag-4_0", "tag-4_1"],
                        },
                    ]
                }
                vm_collection_mock.get_by_id = mock.AsyncMock(
                    side_effect=lambda id: vm_dict.get(id)
                )
                result = await get_affected_vm_id_list(vm_id)

        self.assertEqual(
            set(result),
            expected_vm_ids,
            reason,
        )

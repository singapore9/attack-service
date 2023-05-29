from unittest import IsolatedAsyncioTestCase, mock

from .models import CloudEnvironment, FirewallRule, VMInfo
from .on_startup import prepare_server


def get_mock_path(item: str) -> str:
    return f"internal.on_startup.{item}"


def get_aiter_mock(return_value):
    async_mock = mock.AsyncMock()
    async_mock.__aiter__.return_value = return_value
    return async_mock


class DBOnStartupTestCase(IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.longMessage = True

    @mock.patch(get_mock_path("connect_to_mongo"), mock.AsyncMock())
    @mock.patch(get_mock_path("get_cloud_environment"))
    @mock.patch(get_mock_path("FirewallRuleCollection"))
    @mock.patch(get_mock_path("VirtualMachineCollection"))
    @mock.patch(get_mock_path("TagInfoCollection"))
    async def test(
        self, tag_info_collection, vm_collection, fw_collection, cloud_environment_mock
    ):
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
        vm_collection.get_all_iter.return_value = get_aiter_mock(list(vm_dict.values()))
        vm_collection.get_by_id = mock.AsyncMock(side_effect=lambda id: vm_dict.get(id))

        fw_rule_dict = {
            obj["fw_id"]: FirewallRule.parse_obj(obj)
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
        }

        fw_collection.get_all_iter.return_value = get_aiter_mock(
            list(fw_rule_dict.values())
        )
        fw_collection.get_by_id = mock.AsyncMock(
            side_effect=lambda id: fw_rule_dict.get(id)
        )

        cloud_environment_mock.return_value = mock.AsyncMock(
            return_value=CloudEnvironment(
                machines=list(vm_dict.values()), rules=list(fw_rule_dict.values())
            )
        )
        vm_collection.rewrite = mock.AsyncMock()
        fw_collection.rewrite = mock.AsyncMock()
        tag_info_collection.delete_many = mock.AsyncMock()
        tag_info_collection.add_vm_for_tag = mock.AsyncMock()
        tag_info_collection.add_destination_tag_for_tag = mock.AsyncMock()

        await prepare_server()

        vm_collection.rewrite.assert_awaited_once()
        fw_collection.rewrite.assert_awaited_once()
        tag_info_collection.delete_many.assert_awaited_once()
        tag_info_collection.add_vm_for_tag.assert_has_awaits(
            [
                mock.call(tag, vm_id)
                for (tag, vm_id) in [
                    ("tag-1_0", "vm-1"),
                    ("tag-1_1", "vm-2"),
                    ("tag-2_0", "vm-2"),
                    ("tag-2_1", "vm-3"),
                    ("tag-3_0", "vm-4"),
                    ("tag-3_1", "vm-4"),
                    ("tag-3_2", "vm-5"),
                    ("tag-3_3", "vm-6"),
                    ("tag-4_0", "vm-7"),
                    ("tag-4_1", "vm-7"),
                    ("tag-4_1", "vm-8"),
                ]
            ],
            any_order=True,
        )
        tag_info_collection.add_destination_tag_for_tag.assert_has_awaits(
            [
                mock.call(tag, dest_tag)
                for (tag, dest_tag) in [
                    ("tag-1_0", "tag-1_1"),
                    ("tag-2_0", "tag-2_1"),
                    ("tag-2_0", "tag-2_1"),
                    ("tag-3_0", "tag-3_2"),
                    ("tag-3_1", "tag-3_3"),
                    ("tag-4_0", "tag-4_1"),
                ]
            ],
            any_order=True,
        )

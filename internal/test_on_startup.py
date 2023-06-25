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
    @mock.patch(get_mock_path("StatusCollection"))
    @mock.patch(get_mock_path("TagInfoCollection"))
    @mock.patch(get_mock_path("ResponseInfoCollection"))
    async def test(
        self,
        response_info_collection,
        tag_info_collection,
        status_collection,
        vm_collection,
        fw_collection,
        cloud_environment_mock,
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
                    "source_tag": "tag-1_1",
                    "dest_tag": "tag-1_0",
                },
                {
                    "fw_id": "fw-2_0",
                    "source_tag": "tag-2_1",
                    "dest_tag": "tag-2_0",
                },
                {
                    "fw_id": "fw-2_1",
                    "source_tag": "tag-2_1",
                    "dest_tag": "tag-2_0",
                },
                {
                    "fw_id": "fw-3_0",
                    "source_tag": "tag-3_2",
                    "dest_tag": "tag-3_0",
                },
                {
                    "fw_id": "fw-3_1",
                    "source_tag": "tag-3_3",
                    "dest_tag": "tag-3_1",
                },
                {
                    "fw_id": "fw-4_0",
                    "source_tag": "tag-4_1",
                    "dest_tag": "tag-4_0",
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
        status_collection.delete_many = mock.AsyncMock()
        status_collection.rewrite = mock.AsyncMock()
        response_info_collection.delete_many = mock.AsyncMock()
        tag_info_collection.delete_many = mock.AsyncMock()
        tag_info_insert_one = mock.AsyncMock()
        tag_info_collection.get_collection = mock.AsyncMock(
            return_value=mock.AsyncMock(insert_one=tag_info_insert_one)
        )

        await prepare_server()

        vm_collection.rewrite.assert_awaited_once()
        fw_collection.rewrite.assert_awaited_once()
        response_info_collection.delete_many.assert_awaited_once()
        tag_info_collection.delete_many.assert_awaited_once()

        tag_info_insert_one.assert_has_awaits(
            [
                mock.call(dict(tag=tag, tagged_vm_ids=vm_ids, tags_with_access=[]))
                for tag, vm_ids in [
                    ("tag-1_0", ["vm-1"]),
                    ("tag-1_1", ["vm-2"]),
                    ("tag-2_0", ["vm-2"]),
                    ("tag-2_1", ["vm-3"]),
                    ("tag-3_0", ["vm-4"]),
                    ("tag-3_1", ["vm-4"]),
                    ("tag-3_2", ["vm-5"]),
                    ("tag-3_3", ["vm-6"]),
                    ("tag-4_0", ["vm-7"]),
                    ("tag-4_1", ["vm-7", "vm-8"]),
                ]
            ],
            any_order=True,
        )

        tag_info_insert_one.assert_has_awaits(
            [
                mock.call(
                    dict(tag=dest_tag, tagged_vm_ids=[], tags_with_access=[source_tag])
                )
                for (source_tag, dest_tag) in [
                    ("tag-1_1", "tag-1_0"),
                    ("tag-2_1", "tag-2_0"),
                    ("tag-3_2", "tag-3_0"),
                    ("tag-3_3", "tag-3_1"),
                    ("tag-4_1", "tag-4_0"),
                ]
            ],
            any_order=True,
        )

    @mock.patch(get_mock_path("connect_to_mongo"), mock.AsyncMock())
    @mock.patch(get_mock_path("get_cloud_environment"))
    @mock.patch(get_mock_path("StatusCollection"))
    async def test_with_validation_problem(
        self, status_collection, cloud_environment_mock
    ):
        cloud_environment_mock.side_effect = mock.AsyncMock(
            side_effect=lambda: CloudEnvironment(
                machines=[
                    VMInfo(id="vm1", name="", tags=[]),
                    VMInfo(id="vm1", name="", tags=[]),
                ],
                rules=[],
            )
        )
        status_collection.rewrite = mock.AsyncMock()

        await prepare_server()

        status_collection.rewrite.assert_awaited()
        self.assertEqual(
            status_collection.rewrite.await_args_list[-1][0][0].dict(),
            {
                "ok": False,
                "error_msg": """Cloud Environment was not specified correctly:
1 validation error for CloudEnvironment
vms
  VM IDs should be unique for one environment (type=assertion_error)""",
            },
            "Save info about failed processing",
        )

from unittest import IsolatedAsyncioTestCase, mock

from pydantic import ValidationError

from .extractor import get_cloud_environment
from .models import CloudEnvironment, FirewallRule, VMInfo


class ExtractorTestCase(IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.longMessage = True

    @mock.patch(
        "builtins.open",
        new=mock.mock_open(
            read_data="""{
    "vms": [
        {
            "vm_id": "vm-a211de",
            "name": "jira_server",
            "tags": [
                "ci",
                "dev"
            ]
        },
        {
            "vm_id": "vm-c7bac01a07",
            "name": "bastion",
            "tags": [
                "ssh",
                "dev"
            ]
        }
    ],
    "fw_rules": [
        {
            "fw_id": "fw-82af742",
            "source_tag": "ssh",
            "dest_tag": "dev"
        }
    ]
}"""
        ),
        create=True,
    )
    async def test_extractor_positive(self):
        result = await get_cloud_environment()

        self.assertEqual(
            result,
            CloudEnvironment(
                machines=[
                    VMInfo(id="vm-a211de", name="jira_server", tags=["ci", "dev"]),
                    VMInfo(id="vm-c7bac01a07", name="bastion", tags=["ssh", "dev"]),
                ],
                rules=[FirewallRule(id="fw-82af742", source_tag="ssh", dest_tag="dev")],
            ),
            "Valid JSON with valid models",
        )

    @mock.patch(
        "builtins.open",
        new=mock.mock_open(
            read_data="""{
    "additional_field": [],
    "vms": [],
    "fw_rules": []
}"""
        ),
        create=True,
    )
    async def test_extractor_with_extra_fields(self):
        with self.assertRaises(ValidationError, msg="Valid JSON with incorrect schema"):
            await get_cloud_environment()

    @mock.patch(
        "builtins.open",
        new=mock.mock_open(
            read_data="""{
    "vms": [{
            "vm_id": "id1",
            "name": "n1",
            "tags": [
            ],
            "problemfield": []
        }],
    "fw_rules": []
}"""
        ),
        create=True,
    )
    async def test_extractor_with_extra_inner_fields(self):
        with self.assertRaises(
            ValidationError, msg="Valid JSON with incorrect schema for inner models"
        ):
            await get_cloud_environment()

    @mock.patch(
        "builtins.open",
        new=mock.mock_open(
            read_data="""
    "fw_rules": []
}"""
        ),
        create=True,
    )
    async def test_extractor_with_incorrect_file(self):
        with self.assertRaises(ValidationError, msg="Invalid JSON"):
            await get_cloud_environment()

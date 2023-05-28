from unittest import IsolatedAsyncioTestCase, mock

from parameterized import parameterized
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

    @parameterized.expand(
        (
            (
                "Valid JSON with incorrect schema",
                """
                    {
                        "additional_field": [],
                        "vms": [],
                        "fw_rules": []
                    }""",
            ),
            (
                "Valid JSON with incorrect schema for inner models",
                """
                    {
                        "vms": [{
                                "vm_id": "id1",
                                "name": "n1",
                                "tags": [
                                ],
                                "problemfield": []
                            }],
                        "fw_rules": []
                    }""",
            ),
            (
                "VM IDs should be unique",
                """
                    {
                        "vms": [],
                        "fw_rules": [
                            {
                            "fw_id": "id1",
                            "source_tag": "ssh",
                            "dest_tag": "dev"
                        },
                        {
                            "fw_id": "id1",
                            "source_tag": "ssh",
                            "dest_tag": "dev"
                        }
                        ]
                    }""",
            ),
            (
                "Firewall Rule IDs should be unique",
                """
                    {
                        "vms": [
                            {
                                "vm_id": "vm1",
                                "name": "n1",
                                "tags": []
                            },
                            {
                                "vm_id": "vm1",
                                "name": "n1_1",
                                "tags": []
                            }
                        ],
                        "fw_rules": []
                    }""",
            ),
            (
                "Invalid JSON",
                """
                    {{
                        "fw_rules": []
                    }""",
            ),
        )
    )
    async def test_extractor_validators(self, reason, file_content):
        with mock.patch(
            "builtins.open",
            new=mock.mock_open(read_data=file_content),
            create=True,
        ):
            with self.assertRaises(ValidationError, msg=reason):
                await get_cloud_environment()

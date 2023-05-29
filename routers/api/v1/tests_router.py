import os
from unittest import IsolatedAsyncioTestCase, mock

from fastapi.testclient import TestClient
from httpx import codes
from requests import codes

from main import app


class AttackTestCase(IsolatedAsyncioTestCase):
    @mock.patch("main.CHECK_SERVICE_STATUS", "0")
    async def test_attack_positive(self):
        client = TestClient(app)

        expected_affected_ids = [
            "vm_id1",
        ]
        with mock.patch(
            "routers.api.v1.router.get_affected_vm_id_list"
        ) as get_affected_mock:
            get_affected_mock.return_value = expected_affected_ids
            response = client.get("/api/v1/attack", params={"vm_id": "test"})
        self.assertEqual(response.status_code, codes.OK, "Should return 200")
        self.assertEqual(get_affected_mock.call_count, 1, "Should call logic function")
        self.assertEqual(
            response.json(),
            expected_affected_ids,
            "Should return result of logic function",
        )

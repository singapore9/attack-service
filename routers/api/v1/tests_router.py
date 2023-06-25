import os
from unittest import IsolatedAsyncioTestCase, mock

from fastapi.testclient import TestClient
from httpx import codes
from requests import codes

from main import app


class AttackTestCase(IsolatedAsyncioTestCase):
    @mock.patch("middlewares.check_service_status_middleware.CHECK_SERVICE_STATUS", "0")
    @mock.patch(
        "middlewares.save_service_statistic_middleware.SAVE_SERVICE_STATISTIC", "0"
    )
    async def test_attack_positive(self):
        client = TestClient(app)

        expected_ids_with_access = [
            "vm_id1",
        ]
        with mock.patch(
            "routers.api.v1.router.get_vm_id_list_with_access_to_vm"
        ) as get_vm_id_list_with_access_to_vm_mock:
            get_vm_id_list_with_access_to_vm_mock.return_value = (
                expected_ids_with_access
            )
            response = client.get("/api/v1/attack", params={"vm_id": "test"})
        self.assertEqual(response.status_code, codes.OK, "Should return 200")
        self.assertEqual(
            get_vm_id_list_with_access_to_vm_mock.call_count,
            1,
            "Should call logic function",
        )
        self.assertEqual(
            response.json(),
            expected_ids_with_access,
            "Should return result of logic function",
        )

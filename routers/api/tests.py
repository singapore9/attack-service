from unittest import TestCase, mock

from fastapi.testclient import TestClient
from httpx import codes
from requests import codes

from main import app


class ApiVersionTestCase(TestCase):
    @mock.patch("middlewares.check_service_status_middleware.CHECK_SERVICE_STATUS", "0")
    @mock.patch(
        "middlewares.save_service_statistic_middleware.SAVE_SERVICE_STATISTIC", "0"
    )
    def test_api_version_positive(self):
        client = TestClient(app)

        response = client.get("/api")
        self.assertEqual(response.status_code, codes.OK, "Should return 200")
        self.assertEqual(
            response.json(),
            {"latest": "v1"},
            "Should return the latest api version (v1)",
        )

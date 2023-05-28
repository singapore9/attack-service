from unittest import TestCase

from fastapi.testclient import TestClient
from httpx import codes
from requests import codes

from main import app


class ApiVersionTestCase(TestCase):
    def test_api_version_positive(self):
        client = TestClient(app)

        response = client.get("/api")
        self.assertEqual(response.status_code, codes.OK, "Should return 200")
        self.assertEqual(
            response.json(),
            {"latest": "v1"},
            "Should return the latest api version (v1)",
        )

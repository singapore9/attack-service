from unittest import TestCase

from fastapi.testclient import TestClient
from httpx import codes
from requests import codes

from main import app


class StatusTestCase(TestCase):
    def test_status_positive(self):
        client = TestClient(app)

        response = client.get("/status")
        self.assertEqual(
            response.status_code, codes.OK, "Should return 200 when server is OK"
        )
        self.assertEqual(
            response.json(), {"ok": True}, "Should return status OK when server is OK"
        )

from unittest import TestCase

from fastapi.testclient import TestClient
from httpx import codes
from requests import codes

from main import app


class AttachTestCase(TestCase):
    def test_attack_positive(self):
        client = TestClient(app)

        response = client.get("/api/v1/attack", params={"vm_id": "test"})
        self.assertEqual(response.status_code, codes.OK, "Should return 200")
        self.assertEqual(response.json(), [], "There is no info, empty list")

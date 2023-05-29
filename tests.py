from unittest import IsolatedAsyncioTestCase, mock

from fastapi.testclient import TestClient
from httpx import codes
from requests import codes

from internal.models import StatusModel
from main import app


class StatusTestCase(IsolatedAsyncioTestCase):
    @mock.patch("main.StatusCollection.get_status", mock.AsyncMock(return_value=None))
    def test_status_negative_when_has_no_info_about_status(self):
        client = TestClient(app)

        response = client.get("/status")
        self.assertEqual(
            response.status_code,
            codes.PRECONDITION_REQUIRED,
            "Should return 428 when we don't have info about successful configuration",
        )
        self.assertEqual(
            response.json(),
            {
                "ok": False,
                "error_msg": "Cloud Environment (.json file) configuration was not processed by service before start",
            },
            "Should return status OK when server is OK",
        )

    @mock.patch(
        "main.StatusCollection.get_status",
        mock.AsyncMock(return_value=StatusModel(ok=True, error_msg="")),
    )
    def test_status_positive_when_has_info_about_status(self):
        client = TestClient(app)

        response = client.get("/status")
        self.assertEqual(
            response.status_code,
            codes.OK,
            "Should return OK when server is OK and configuration was successful",
        )
        self.assertEqual(
            response.json(),
            {"ok": True, "error_msg": ""},
            "Should return status not OK when server is OK and config was processed",
        )

    @mock.patch(
        "main.StatusCollection.get_status",
        mock.AsyncMock(
            return_value=StatusModel(ok=False, error_msg="Validation failed")
        ),
    )
    def test_status_negative_when_has_info_about_error(self):
        client = TestClient(app)

        response = client.get("/status")
        self.assertEqual(
            response.status_code,
            codes.PRECONDITION_REQUIRED,
            "Should return 428 when configuration failed",
        )
        self.assertEqual(
            response.json(),
            {"ok": False, "error_msg": "Validation failed"},
            "Should return status not OK when server is OK but .json has problems",
        )

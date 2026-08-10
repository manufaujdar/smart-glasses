import http.client
import json
import sys
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "device-contracts"))
sys.path.insert(0, str(ROOT / "tools"))

from device_gateway import DeviceGateway, create_server  # noqa: E402


class DeviceGatewayTests(unittest.TestCase):
    def setUp(self):
        self.server = create_server(0, DeviceGateway())
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def request(self, method, path, body=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port)
        encoded = None if body is None else json.dumps(body)
        headers = {"content-type": "application/json"} if encoded is not None else {}
        connection.request(method, path, body=encoded, headers=headers)
        response = connection.getresponse()
        payload = json.loads(response.read())
        connection.close()
        return response.status, payload

    def test_health_state_command_and_event_history(self):
        status, health = self.request("GET", "/health")
        self.assertEqual(status, 200)
        self.assertTrue(health["synthetic"])

        status, result = self.request(
            "POST",
            "/api/command",
            {"name": "device.connect", "command_id": "connect-1"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["event"]["name"], "device.connected")
        self.assertEqual(result["state"]["connection_state"], "connected")

        status, result = self.request(
            "POST",
            "/api/command",
            {"name": "camera.take_photo", "command_id": "photo-1"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(result["event"]["payload"]["media_id"], "photo-0001")
        self.assertEqual(result["state"]["photo_count"], 1)

        status, history = self.request("GET", "/api/events")
        self.assertEqual(status, 200)
        self.assertEqual([event["name"] for event in history["events"]], [
            "device.connected", "camera.photo_captured"
        ])

    def test_replay_is_idempotent_and_reset_clears_state(self):
        self.request("POST", "/api/command", {"name": "device.connect", "command_id": "connect-1"})
        first_status, first = self.request(
            "POST", "/api/command", {"name": "camera.take_photo", "command_id": "photo-1"}
        )
        replay_status, replay = self.request(
            "POST", "/api/command", {"name": "camera.take_photo", "command_id": "photo-1"}
        )
        self.assertEqual(first_status, replay_status, 200)
        self.assertEqual(first, replay)
        self.assertEqual(first["state"]["photo_count"], 1)

        status, reset = self.request("POST", "/api/reset", {})
        self.assertEqual(status, 200)
        self.assertEqual(reset["state"]["connection_state"], "disconnected")
        self.assertEqual(reset["state"]["photo_count"], 0)

    def test_invalid_commands_fail_closed(self):
        status, body = self.request(
            "POST", "/api/command", {"name": "clinical.navigate", "command_id": "unsafe"}
        )
        self.assertEqual(status, 400)
        self.assertEqual(body["error"], "unsupported command")

        status, body = self.request("POST", "/api/command", {"name": "device.connect"})
        self.assertEqual(status, 400)
        self.assertIn("command_id", body["error"])


if __name__ == "__main__":
    unittest.main()

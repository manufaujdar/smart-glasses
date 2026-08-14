import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "device-contracts"))
sys.path.insert(0, str(ROOT / "packages"))
sys.path.insert(0, str(ROOT / "tools"))

try:
    from fastapi.testclient import TestClient
    from device_runtime import DeviceHub, SimulatorAdapter
    from integration_server import create_app
except ImportError:
    TestClient = None


@unittest.skipIf(TestClient is None, "integration dependencies are not installed")
class IntegrationServerTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_app(DeviceHub([SimulatorAdapter()])))

    def test_adapter_discovery_command_and_security_headers(self):
        adapters = self.client.get("/api/adapters")
        self.assertEqual(adapters.status_code, 200)
        self.assertEqual(adapters.json()["active_adapter"], "simulator")
        self.assertEqual(adapters.headers["x-frame-options"], "DENY")

        discovered = self.client.post("/api/discover", json={"timeout_seconds": 1})
        self.assertTrue(discovered.json()["devices"][0]["synthetic"])

        connected = self.client.post("/api/command", json={
            "name": "device.connect", "command_id": "connect-1", "payload": {},
        })
        self.assertEqual(connected.status_code, 200)
        self.assertEqual(connected.json()["state"]["connection_state"], "connected")

    def test_unknown_command_fails_closed(self):
        response = self.client.post("/api/command", json={
            "name": "clinical.navigate", "command_id": "unsafe", "payload": {},
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "unsupported command")

    def test_request_size_is_bounded(self):
        response = self.client.post(
            "/api/command",
            content=b"x" * 70_000,
            headers={"content-type": "application/json"},
        )
        self.assertEqual(response.status_code, 413)

    def test_websocket_receives_state_snapshot(self):
        with self.client.websocket_connect("/ws/events") as socket:
            message = socket.receive_json()
            self.assertEqual(message["type"], "state.snapshot")
            self.assertTrue(message["state"]["synthetic"])


if __name__ == "__main__":
    unittest.main()

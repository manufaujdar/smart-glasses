#!/usr/bin/env python3
"""Run a synthetic surgeon-observation workflow through device and session layers."""

import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "device-contracts"))
sys.path.insert(0, str(ROOT / "packages" / "surgical-workflows"))
sys.path.insert(0, str(ROOT / "tools"))

from device_contracts import DeviceCommand  # noqa: E402
from device_simulator import SimulatedGlasses  # noqa: E402
from surgical_session import SurgicalSession, complete_all_preflight_gates  # noqa: E402


class SyntheticObservationController:
    """Single reducer boundary that couples device faults to session safe state."""

    def __init__(self, device: SimulatedGlasses, session: SurgicalSession) -> None:
        self.device = device
        self.session = session
        self._propagated_device_events: set[tuple[str, str]] = set()

    def execute_device(self, command: DeviceCommand) -> list[dict]:
        event = self.device.execute(command)
        output = [asdict(event)]
        event_key = (event.command_id or "", event.name)
        if event.name == "device.disconnected" and event_key not in self._propagated_device_events:
            self._propagated_device_events.add(event_key)
            output.append(asdict(self.session.device_disconnected()))
        return output


def run_synthetic_observation() -> list[dict]:
    device = SimulatedGlasses("SIM-SURGICAL-GLASSES-001")
    session = SurgicalSession()
    controller = SyntheticObservationController(device, session)
    output: list[dict] = []

    output.extend(controller.execute_device(DeviceCommand("device.connect")))
    output.append(asdict(session.start_preflight()))
    output.extend(asdict(event) for event in complete_all_preflight_gates(session))
    output.append(
        asdict(
            session.arm(
                device.battery,
                device.state.value == "connected",
                device.capabilities,
            )
        )
    )
    output.append(asdict(session.start_observation(recording=True)))
    output.append(asdict(session.clear_view()))
    output.extend(controller.execute_device(DeviceCommand("device.disconnect")))
    return output


if __name__ == "__main__":
    for event in run_synthetic_observation():
        print(json.dumps(event, sort_keys=True))

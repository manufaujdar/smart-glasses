"""Non-clinical surgical-observation workflow and fail-safe state model."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from math import isfinite
from typing import Any, Mapping


class SurgicalSessionState(str, Enum):
    IDLE = "idle"
    PREFLIGHT = "preflight"
    READY = "ready"
    OBSERVING = "observing"
    PAUSED = "paused"
    SAFE_STOP = "safe_stop"
    COMPLETED = "completed"


class PreflightGate(str, Enum):
    CONSENT_AUTHORIZED = "consent_authorized"
    TEAM_BRIEF_COMPLETE = "team_brief_complete"
    PRIVACY_APPROVED = "privacy_approved"
    DEVICE_READY = "device_ready"
    CAPTURE_INDICATOR_VERIFIED = "capture_indicator_verified"


@dataclass(frozen=True)
class SessionEvent:
    name: str
    session_id: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class SurgicalSession:
    """Fail-closed controller for synthetic observation and tele-mentoring trials."""

    MINIMUM_BATTERY_PERCENT = 30
    ACTIVE_SAFE_STOP_BATTERY_PERCENT = 15

    def __init__(self, session_id: str = "SYNTHETIC-SESSION-001") -> None:
        if not session_id.startswith("SYNTHETIC-"):
            raise ValueError("development sessions require a SYNTHETIC- identifier")
        self.session_id = session_id
        self.state = SurgicalSessionState.IDLE
        self.gates: set[PreflightGate] = set()
        self.recording = False
        self.streaming = False
        self.overlays_enabled = False
        self.connected = False
        self.capabilities: set[str] = set()
        self.capture_indicator_state = "unknown"
        self.battery_percent: int | None = None
        self.safe_stop_reason: str | None = None
        self.events: list[SessionEvent] = []

    def start_preflight(self) -> SessionEvent:
        if self.state != SurgicalSessionState.IDLE:
            return self._reject("preflight.invalid_state")
        self.state = SurgicalSessionState.PREFLIGHT
        return self._emit("preflight.started")

    def confirm_gate(self, gate: PreflightGate) -> SessionEvent:
        if self.state != SurgicalSessionState.PREFLIGHT:
            return self._reject("preflight.not_active")
        if (
            gate is PreflightGate.CAPTURE_INDICATOR_VERIFIED
            and self.capture_indicator_state != "visible"
        ):
            return self._reject("capture_indicator.not_verified")
        self.gates.add(gate)
        return self._emit("preflight.gate_confirmed", {"gate": gate.value})

    def arm(
        self,
        battery_percent: int,
        connected: bool = False,
        capabilities: set[str] | None = None,
    ) -> SessionEvent:
        if self.state != SurgicalSessionState.PREFLIGHT:
            return self._reject("session.invalid_state")
        missing = sorted(gate.value for gate in set(PreflightGate) - self.gates)
        if missing:
            return self._reject("preflight.incomplete", {"missing": missing})
        if not connected:
            return self._reject("device.not_connected")
        if not self._valid_battery(battery_percent):
            return self._reject("device.invalid_battery")
        if self.capture_indicator_state != "visible":
            return self._reject("capture_indicator.not_verified")
        if not capabilities:
            return self._reject("device.capabilities_unavailable")
        if battery_percent < self.MINIMUM_BATTERY_PERCENT:
            return self._reject(
                "device.low_battery",
                {"battery_percent": battery_percent, "minimum": self.MINIMUM_BATTERY_PERCENT},
            )
        self.connected = True
        self.capabilities = set(capabilities)
        self.battery_percent = battery_percent
        self.state = SurgicalSessionState.READY
        return self._emit("session.ready", {"battery_percent": battery_percent})

    def start_observation(self, recording: bool = False, streaming: bool = False) -> SessionEvent:
        if self.state != SurgicalSessionState.READY:
            return self._reject("session.not_ready")
        if not recording and not streaming:
            return self._reject("session.no_active_mode")
        missing = self._missing_mode_capabilities(recording, streaming)
        if missing:
            return self._reject("device.capability_missing", {"missing": missing})
        if not self.connected:
            return self._reject("device.not_connected")
        if self.capture_indicator_state != "visible":
            return self._reject("capture_indicator.not_verified")
        self.recording = recording
        self.streaming = streaming
        self.state = SurgicalSessionState.OBSERVING
        return self._emit(
            "session.observation_started",
            {"recording": recording, "streaming": streaming},
        )

    def pause(self) -> SessionEvent:
        if self.state != SurgicalSessionState.OBSERVING:
            return self._reject("session.not_observing")
        self.recording = False
        self.streaming = False
        self.overlays_enabled = False
        self.state = SurgicalSessionState.PAUSED
        return self._emit("session.paused")

    def resume(self, recording: bool = False, streaming: bool = False) -> SessionEvent:
        if self.state != SurgicalSessionState.PAUSED:
            return self._reject("session.not_paused")
        if not recording and not streaming:
            return self._reject("session.no_active_mode")
        missing = self._missing_mode_capabilities(recording, streaming)
        if missing:
            return self._reject("device.capability_missing", {"missing": missing})
        if (
            not self.connected
            or self.capture_indicator_state != "visible"
            or self.battery_percent is None
            or self.battery_percent <= self.ACTIVE_SAFE_STOP_BATTERY_PERCENT
        ):
            return self._safe_stop("resume_preconditions_failed")
        self.recording = recording
        self.streaming = streaming
        self.state = SurgicalSessionState.OBSERVING
        return self._emit(
            "session.resumed", {"recording": recording, "streaming": streaming}
        )

    def set_advisory_overlay(self, enabled: bool) -> SessionEvent:
        if enabled and self.state != SurgicalSessionState.OBSERVING:
            return self._reject("overlay.session_not_observing")
        self.overlays_enabled = enabled
        return self._emit("overlay.changed", {"enabled": enabled, "advisory_only": True})

    def clear_view(self) -> SessionEvent:
        self.overlays_enabled = False
        return self._emit("display.clear_view")

    def device_disconnected(self) -> SessionEvent:
        self.connected = False
        if self.state in {SurgicalSessionState.IDLE, SurgicalSessionState.COMPLETED}:
            return self._reject("device.disconnect_outside_session")
        return self._safe_stop("device_disconnected")

    def battery_changed(self, battery_percent: int | None) -> SessionEvent:
        if not self._valid_battery(battery_percent):
            if self.state in {
                SurgicalSessionState.READY,
                SurgicalSessionState.OBSERVING,
                SurgicalSessionState.PAUSED,
            }:
                return self._safe_stop("battery_telemetry_untrusted")
            return self._reject("device.invalid_battery")
        self.battery_percent = battery_percent
        if (
            self.state in {SurgicalSessionState.READY, SurgicalSessionState.OBSERVING, SurgicalSessionState.PAUSED}
            and battery_percent <= self.ACTIVE_SAFE_STOP_BATTERY_PERCENT
        ):
            return self._safe_stop(
                "critical_battery",
                {"battery_percent": battery_percent},
            )
        return self._emit("device.battery_changed", {"battery_percent": battery_percent})

    def capture_indicator_changed(self, visible: bool | None) -> SessionEvent:
        self.capture_indicator_state = "visible" if visible is True else "hidden" if visible is False else "unknown"
        if visible is True and self.state == SurgicalSessionState.PREFLIGHT:
            self.gates.add(PreflightGate.CAPTURE_INDICATOR_VERIFIED)
        elif visible is not True:
            self.gates.discard(PreflightGate.CAPTURE_INDICATOR_VERIFIED)
            if self.state in {
                SurgicalSessionState.READY,
                SurgicalSessionState.OBSERVING,
                SurgicalSessionState.PAUSED,
            }:
                return self._safe_stop("capture_indicator_lost")
        return self._emit("capture_indicator.changed", {"state": self.capture_indicator_state})

    def capabilities_changed(self, capabilities: set[str]) -> SessionEvent:
        self.capabilities = set(capabilities)
        required = self._missing_mode_capabilities(self.recording, self.streaming)
        if self.state == SurgicalSessionState.OBSERVING and required:
            return self._safe_stop("device.capability_lost", {"missing": required})
        return self._emit("device.capabilities_changed", {"capabilities": sorted(capabilities)})

    def end(self) -> SessionEvent:
        if self.state not in {
            SurgicalSessionState.READY,
            SurgicalSessionState.OBSERVING,
            SurgicalSessionState.PAUSED,
        }:
            return self._reject("session.cannot_complete_from_state")
        self._stop_outputs()
        self.state = SurgicalSessionState.COMPLETED
        return self._emit("session.completed")

    def _stop_outputs(self) -> None:
        self.recording = False
        self.streaming = False
        self.overlays_enabled = False

    def _safe_stop(
        self,
        reason: str,
        details: Mapping[str, Any] | None = None,
    ) -> SessionEvent:
        if self.state == SurgicalSessionState.SAFE_STOP:
            return self._emit(
                "session.safe_stop_fault_recorded",
                {"reason": reason, "primary_reason": self.safe_stop_reason},
            )
        self._stop_outputs()
        self.safe_stop_reason = reason
        self.state = SurgicalSessionState.SAFE_STOP
        payload: dict[str, Any] = {"reason": reason}
        payload.update(details or {})
        return self._emit("session.safe_stopped", payload)

    @staticmethod
    def _required_mode_capabilities(recording: bool, streaming: bool) -> set[str]:
        required: set[str] = set()
        if recording:
            required.add("camera.video")
        if streaming:
            required.add("telepresence.stream")
        return required

    def _missing_mode_capabilities(self, recording: bool, streaming: bool) -> list[str]:
        return sorted(self._required_mode_capabilities(recording, streaming) - self.capabilities)

    @staticmethod
    def _valid_battery(value: object) -> bool:
        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and isfinite(value)
            and 0 <= value <= 100
        )

    def _reject(self, reason: str, details: Mapping[str, Any] | None = None) -> SessionEvent:
        payload: dict[str, Any] = {"reason": reason}
        payload.update(details or {})
        return self._emit("command.rejected", payload)

    def _emit(self, name: str, payload: Mapping[str, Any] | None = None) -> SessionEvent:
        event = SessionEvent(name=name, session_id=self.session_id, payload=payload or {})
        self.events.append(event)
        return event


def complete_all_preflight_gates(session: SurgicalSession) -> list[SessionEvent]:
    events = [
        session.confirm_gate(gate)
        for gate in PreflightGate
        if gate is not PreflightGate.CAPTURE_INDICATOR_VERIFIED
    ]
    events.append(session.capture_indicator_changed(True))
    return events

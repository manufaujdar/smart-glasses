"""Local-only SQLite storage for small, validated geometry summaries.

The store deliberately rejects images, raw depth grids, and patient identifiers.
It is a prototype persistence boundary, not a production PHI repository.
"""

from __future__ import annotations

import json
import math
import re
import secrets
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any


class StorageValidationError(ValueError):
    """Raised when a record is not safe for the local summary store."""


_OPAQUE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
_SENSOR_MODES = {"camera", "professional_lidar"}
_ACCURACY_TIERS = {"low", "high"}
_FORBIDDEN_KEYS = {"depth_mm", "depth_grid", "image", "image_data", "photo", "patient_name", "mrn", "date_of_birth"}
_MEASUREMENT_KEYS = {
    "median_depth_offset_mm",
    "p95_depth_offset_mm",
    "maximum_depth_offset_mm",
    "mean_positive_depth_offset_mm",
    "projected_area_mm2",
    "estimated_positive_volume_mm3",
    "background_median_depth_mm",
    "background_mad_mm",
    "roi_residual_mad_mm",
    "background_outliers_trimmed",
    "plane_tilt_deg",
    "repeatability_proxy_mm",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _opaque(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _OPAQUE_ID.fullmatch(value):
        raise StorageValidationError(f"{field} must be an opaque ASCII identifier of 1-80 characters")
    return value


def _timestamp(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise StorageValidationError("captured_at must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError as exc:
        raise StorageValidationError("captured_at must be a valid ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise StorageValidationError("captured_at must include a timezone")
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def validate_record(record: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise StorageValidationError("record must be a JSON object")
    if _FORBIDDEN_KEYS.intersection(record):
        raise StorageValidationError("raw images, depth grids, and direct identifiers are not accepted")
    for required in ("wound_id", "capture_id", "captured_at", "sensor_mode", "accuracy_tier", "measurements", "quality"):
        if required not in record:
            raise StorageValidationError(f"record is missing {required}")
    wound_id = _opaque(record["wound_id"], "wound_id")
    capture_id = _opaque(record["capture_id"], "capture_id")
    sensor_mode = record["sensor_mode"]
    accuracy_tier = record["accuracy_tier"]
    if sensor_mode not in _SENSOR_MODES:
        raise StorageValidationError("sensor_mode must be camera or professional_lidar")
    if accuracy_tier not in _ACCURACY_TIERS:
        raise StorageValidationError("accuracy_tier must be low or high")
    expected_tier = "low" if sensor_mode == "camera" else "high"
    if accuracy_tier != expected_tier:
        raise StorageValidationError(f"{sensor_mode} records must use the {expected_tier} accuracy tier")
    measurements = record["measurements"]
    if not isinstance(measurements, dict) or set(measurements) - _MEASUREMENT_KEYS:
        raise StorageValidationError("measurements contain unsupported fields")
    if not measurements:
        raise StorageValidationError("measurements must contain at least one allowed metric")
    clean_measurements: dict[str, float] = {}
    for key, value in measurements.items():
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)):
            raise StorageValidationError(f"measurement {key} must be finite numeric data")
        clean_measurements[key] = float(value)
    quality = record["quality"]
    if not isinstance(quality, dict):
        raise StorageValidationError("quality must be an object")
    quality_score = quality.get("engineering_quality_score")
    if not isinstance(quality_score, (int, float)) or not 0 <= float(quality_score) <= 1:
        raise StorageValidationError("quality.engineering_quality_score must be between zero and one")
    flags = quality.get("flags", [])
    if not isinstance(flags, list) or not all(isinstance(flag, str) and len(flag) <= 80 for flag in flags):
        raise StorageValidationError("quality.flags must be a list of short strings")
    clean_quality = {
        "engineering_quality_score": float(quality_score),
        "flags": flags,
        "score_definition": str(quality.get("score_definition", "engineering data-quality indicator"))[:200],
    }
    clean = {
        "wound_id": wound_id,
        "capture_id": capture_id,
        "captured_at": _timestamp(record["captured_at"]),
        "sensor_mode": sensor_mode,
        "accuracy_tier": accuracy_tier,
        "measurements": clean_measurements,
        "quality": clean_quality,
    }
    encoded = json.dumps(clean, sort_keys=True, allow_nan=False, separators=(",", ":"))
    if len(encoded.encode("utf-8")) > 32_000:
        raise StorageValidationError("numeric record is too large")
    return clean


class LocalRecordStore:
    """SQLite-backed store for geometry summaries and minimal audit events."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.database_path, check_same_thread=False)
        self._lock = RLock()
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS records (
                record_id TEXT PRIMARY KEY,
                wound_id TEXT NOT NULL,
                capture_id TEXT NOT NULL,
                sensor_mode TEXT NOT NULL,
                captured_at TEXT NOT NULL,
                record_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(wound_id, capture_id, sensor_mode)
            );
            CREATE INDEX IF NOT EXISTS records_wound_time
                ON records(wound_id, sensor_mode, captured_at);
            CREATE TABLE IF NOT EXISTS audit_events (
                event_id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                record_id TEXT,
                created_at TEXT NOT NULL,
                metadata_json TEXT NOT NULL
            );
            """
        )
        self.connection.commit()

    def _audit(self, event_type: str, record_id: str | None, metadata: dict[str, Any] | None = None) -> None:
        safe_metadata = metadata or {}
        self.connection.execute(
            "INSERT INTO audit_events(event_id, event_type, record_id, created_at, metadata_json) VALUES (?, ?, ?, ?, ?)",
            (uuid.uuid4().hex, event_type, record_id, _now(), json.dumps(safe_metadata, sort_keys=True)),
        )

    def save(self, record: dict[str, Any]) -> dict[str, Any]:
        clean = validate_record(record)
        with self._lock:
            record_id = uuid.uuid4().hex
            encoded = json.dumps(clean, sort_keys=True, allow_nan=False)
            self.connection.execute(
                """
                INSERT INTO records(record_id, wound_id, capture_id, sensor_mode, captured_at, record_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(wound_id, capture_id, sensor_mode) DO UPDATE SET
                    captured_at=excluded.captured_at,
                    record_json=excluded.record_json,
                    created_at=excluded.created_at
                """,
                (record_id, clean["wound_id"], clean["capture_id"], clean["sensor_mode"], clean["captured_at"], encoded, _now()),
            )
            row = self.connection.execute(
                "SELECT record_id FROM records WHERE wound_id=? AND capture_id=? AND sensor_mode=?",
                (clean["wound_id"], clean["capture_id"], clean["sensor_mode"]),
            ).fetchone()
            actual_id = str(row["record_id"])
            self._audit("record_saved", actual_id, {"sensor_mode": clean["sensor_mode"]})
            self.connection.commit()
            return {"record_id": actual_id, **clean}

    def list(self, wound_id: str | None = None, sensor_mode: str | None = None) -> list[dict[str, Any]]:
        clauses: list[str] = []
        values: list[Any] = []
        if wound_id is not None:
            clauses.append("wound_id=?")
            values.append(_opaque(wound_id, "wound_id"))
        if sensor_mode is not None:
            if sensor_mode not in _SENSOR_MODES:
                raise StorageValidationError("invalid sensor_mode")
            clauses.append("sensor_mode=?")
            values.append(sensor_mode)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._lock:
            rows = self.connection.execute(
                f"SELECT record_id, record_json FROM records{where} ORDER BY captured_at ASC, record_id ASC", values
            ).fetchall()
            return [{"record_id": str(row["record_id"]), **json.loads(row["record_json"])} for row in rows]

    def delete(self, record_id: str) -> bool:
        if not isinstance(record_id, str) or not re.fullmatch(r"^[a-f0-9]{32}$", record_id):
            raise StorageValidationError("record_id is invalid")
        with self._lock:
            cursor = self.connection.execute("DELETE FROM records WHERE record_id=?", (record_id,))
            if cursor.rowcount:
                self._audit("record_deleted", record_id)
                self.connection.commit()
                return True
            return False

    def audit(self, limit: int = 100) -> list[dict[str, Any]]:
        safe_limit = max(1, min(int(limit), 500))
        with self._lock:
            rows = self.connection.execute(
                "SELECT event_id, event_type, record_id, created_at, metadata_json FROM audit_events ORDER BY created_at DESC LIMIT ?",
                (safe_limit,),
            ).fetchall()
            return [
                {
                    "event_id": row["event_id"],
                    "event_type": row["event_type"],
                    "record_id": row["record_id"],
                    "created_at": row["created_at"],
                    "metadata": json.loads(row["metadata_json"]),
                }
                for row in rows
            ]

    def close(self) -> None:
        with self._lock:
            self.connection.close()


def token_is_valid(expected: str | None, supplied: str | None) -> bool:
    if expected is None:
        return True
    if not supplied:
        return False
    return secrets.compare_digest(expected, supplied)

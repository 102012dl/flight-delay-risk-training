"""Validated operational flight records and CSV ingestion."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Mapping

from .classifier import classify_delay_risk


REQUIRED_FIELDS = (
    "flight_id",
    "scheduled_departure",
    "delay_minutes",
    "weather_risk",
    "crew_issue",
)


class OperationalDataValidationError(ValueError):
    """Raised when an operational record violates the data contract."""


@dataclass(frozen=True)
class FlightOperationalRecord:
    """Analysis-ready representation of one validated operational record."""

    flight_id: str
    scheduled_departure: datetime
    delay_minutes: int
    weather_risk: bool
    crew_issue: bool

    @property
    def risk_category(self) -> str:
        """Classify this record using the unchanged Week-1 classifier."""
        return classify_delay_risk(
            self.delay_minutes,
            self.weather_risk,
            self.crew_issue,
        )


def _parse_departure(value: object) -> datetime:
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str) or not value:
        raise OperationalDataValidationError(
            "scheduled_departure must be an ISO-8601 string or datetime"
        )
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise OperationalDataValidationError(
            "scheduled_departure must be ISO-8601-compatible"
        ) from exc


def _parse_csv_bool(value: object, field: str) -> bool:
    if not isinstance(value, str) or value not in {"true", "false"}:
        raise OperationalDataValidationError(
            f"{field} must be the lowercase string 'true' or 'false'"
        )
    return value == "true"


def validate_record(record: Mapping[str, object]) -> FlightOperationalRecord:
    """Validate and convert one mapping without silently repairing values."""
    missing = [field for field in REQUIRED_FIELDS if field not in record]
    if missing:
        raise OperationalDataValidationError(
            f"missing required field(s): {', '.join(missing)}"
        )

    flight_id = record["flight_id"]
    if not isinstance(flight_id, str) or not flight_id.strip():
        raise OperationalDataValidationError("flight_id must be a non-empty string")

    delay = record["delay_minutes"]
    if not isinstance(delay, int) or isinstance(delay, bool):
        raise OperationalDataValidationError("delay_minutes must be an integer")
    if delay < 0:
        raise OperationalDataValidationError("delay_minutes must be >= 0")

    weather_risk = record["weather_risk"]
    crew_issue = record["crew_issue"]
    if not isinstance(weather_risk, bool):
        raise OperationalDataValidationError("weather_risk must be a boolean")
    if not isinstance(crew_issue, bool):
        raise OperationalDataValidationError("crew_issue must be a boolean")

    return FlightOperationalRecord(
        flight_id=flight_id,
        scheduled_departure=_parse_departure(record["scheduled_departure"]),
        delay_minutes=delay,
        weather_risk=weather_risk,
        crew_issue=crew_issue,
    )


def load_operational_csv(path: str | Path) -> list[FlightOperationalRecord]:
    """Load, validate, and return all records from an operational CSV file."""
    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise OperationalDataValidationError("CSV must include a header")
        missing = [field for field in REQUIRED_FIELDS if field not in reader.fieldnames]
        if missing:
            raise OperationalDataValidationError(
                f"missing required CSV column(s): {', '.join(missing)}"
            )

        records: list[FlightOperationalRecord] = []
        seen_ids: set[str] = set()
        for row_number, row in enumerate(reader, start=2):
            if None in row:
                raise OperationalDataValidationError(
                    f"row {row_number} has more values than the CSV header"
                )
            raw = {field: row[field] for field in REQUIRED_FIELDS}
            raw["delay_minutes"] = _parse_delay_csv(raw["delay_minutes"], row_number)
            raw["weather_risk"] = _parse_csv_bool(raw["weather_risk"], "weather_risk")
            raw["crew_issue"] = _parse_csv_bool(raw["crew_issue"], "crew_issue")
            record = validate_record(raw)
            if record.flight_id in seen_ids:
                raise OperationalDataValidationError(
                    f"duplicate flight_id: {record.flight_id}"
                )
            seen_ids.add(record.flight_id)
            records.append(record)
        return records


def _parse_delay_csv(value: object, row_number: int) -> int:
    if not isinstance(value, str) or not value or not value.isdecimal():
        raise OperationalDataValidationError(
            f"row {row_number}: delay_minutes must be an integer"
        )
    return int(value)


def classify_operational_record(record: FlightOperationalRecord) -> str:
    """Return the Week-1 risk category for a validated operational record."""
    if not isinstance(record, FlightOperationalRecord):
        raise TypeError("record must be a FlightOperationalRecord")
    return record.risk_category

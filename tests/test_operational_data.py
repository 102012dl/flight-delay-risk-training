from pathlib import Path

import pytest

from flight_delay_risk import (
    FlightOperationalRecord,
    OperationalDataValidationError,
    classify_operational_record,
    load_operational_csv,
    validate_record,
)


BASE = {
    "flight_id": "FL-TEST",
    "scheduled_departure": "2026-01-01T08:00:00+00:00",
    "delay_minutes": 29,
    "weather_risk": False,
    "crew_issue": False,
}


def record(**changes: object) -> dict[str, object]:
    value = BASE.copy()
    value.update(changes)
    return value


def test_valid_single_record_is_structured() -> None:
    result = validate_record(record())
    assert isinstance(result, FlightOperationalRecord)
    assert result.delay_minutes == 29


def test_valid_csv_ingestion() -> None:
    path = Path(__file__).parents[1] / "data" / "operational_flights.csv"
    results = load_operational_csv(path)
    assert len(results) == 22


@pytest.mark.parametrize("delay", [30, 60, 120])
def test_boundary_records_are_accepted(delay: int) -> None:
    result = validate_record(record(delay_minutes=delay))
    assert result.delay_minutes == delay


def test_boundary_at_60_with_risk_is_high() -> None:
    result = validate_record(record(delay_minutes=60, weather_risk=True))
    assert classify_operational_record(result) == "HIGH"


def test_boundary_at_120_is_high() -> None:
    result = validate_record(record(delay_minutes=120))
    assert classify_operational_record(result) == "HIGH"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("delay_minutes", -1),
        ("delay_minutes", "60"),
        ("delay_minutes", True),
        ("weather_risk", "true"),
        ("crew_issue", 1),
        ("flight_id", ""),
        ("scheduled_departure", "not-a-date"),
    ],
)
def test_invalid_record_values_are_rejected(field: str, value: object) -> None:
    with pytest.raises(OperationalDataValidationError):
        validate_record(record(**{field: value}))


def test_missing_required_field_is_rejected() -> None:
    invalid = record()
    del invalid["crew_issue"]
    with pytest.raises(OperationalDataValidationError):
        validate_record(invalid)


def test_duplicate_flight_id_is_rejected() -> None:
    path = Path(__file__).parent / "fixtures" / "duplicate.csv"
    with pytest.raises(OperationalDataValidationError, match="duplicate"):
        load_operational_csv(path)


def test_csv_invalid_delay_type_is_rejected() -> None:
    path = Path(__file__).parent / "fixtures" / "invalid_delay.csv"
    with pytest.raises(OperationalDataValidationError):
        load_operational_csv(path)

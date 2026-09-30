"""Contract and integration tests for the typed HTTP boundary."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from flight_delay_risk import api


@pytest.fixture()
def client() -> TestClient:
    return TestClient(api.app)


def test_health_is_deterministic_and_dependency_free(client: TestClient) -> None:
    assert client.get("/health").status_code == 200
    assert client.get("/health").json() == {"status": "ok"}


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        ({"delay_minutes": 0, "weather_risk": False, "crew_issue": False}, "LOW"),
        ({"delay_minutes": 30, "weather_risk": False, "crew_issue": False}, "MEDIUM"),
        ({"delay_minutes": 120, "weather_risk": False, "crew_issue": False}, "HIGH"),
        ({"delay_minutes": 60, "weather_risk": True, "crew_issue": False}, "HIGH"),
    ],
)
def test_risk_contract_preserves_classifier_boundaries(
    client: TestClient, payload: dict[str, object], expected: str
) -> None:
    response = client.post("/risk", json=payload)
    assert response.status_code == 200
    assert response.json() == {"risk_category": expected}


@pytest.mark.parametrize(
    "payload",
    [
        {"delay_minutes": -1, "weather_risk": False, "crew_issue": False},
        {"delay_minutes": 30, "weather_risk": 1, "crew_issue": False},
        {"delay_minutes": 30, "weather_risk": False, "crew_issue": 0},
        {"delay_minutes": "30", "weather_risk": False, "crew_issue": False},
        {"delay_minutes": True, "weather_risk": False, "crew_issue": False},
    ],
)
def test_invalid_values_are_rejected_without_coercion(
    client: TestClient, payload: dict[str, object]
) -> None:
    assert client.post("/risk", json=payload).status_code == 422


def test_missing_fields_and_extra_fields_are_rejected(client: TestClient) -> None:
    missing = {"delay_minutes": 10, "weather_risk": False}
    extra = {"delay_minutes": 10, "weather_risk": False, "crew_issue": False, "secret": "x"}
    assert client.post("/risk", json=missing).status_code == 422
    assert client.post("/risk", json=extra).status_code == 422


def test_malformed_json_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/risk", content='{"delay_minutes": 10,', headers={"content-type": "application/json"}
    )
    assert response.status_code == 422


def test_repeated_requests_are_deterministic_and_have_no_filesystem_side_effects(
    client: TestClient,
) -> None:
    root = Path.cwd()
    before = sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())
    payload = {"delay_minutes": 59, "weather_risk": True, "crew_issue": False}
    responses = [client.post("/risk", json=payload).json() for _ in range(5)]
    assert responses == [{"risk_category": "MEDIUM"}] * 5
    after = sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())
    assert after == before


def test_risk_delegates_to_existing_classifier(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[tuple[int, bool, bool]] = []

    def fake_classifier(delay: int, weather: bool, crew: bool) -> str:
        calls.append((delay, weather, crew))
        return "HIGH"

    monkeypatch.setattr(api, "classify_delay_risk", fake_classifier)
    response = client.post(
        "/risk", json={"delay_minutes": 12, "weather_risk": True, "crew_issue": False}
    )
    assert response.status_code == 200
    assert response.json() == {"risk_category": "HIGH"}
    assert calls == [(12, True, False)]


def test_unknown_route_does_not_create_external_dependency() -> None:
    assert not hasattr(api, "requests")

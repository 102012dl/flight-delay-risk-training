from pathlib import Path

import pandas as pd
import pytest

from flight_delay_risk import load_operational_csv
from flight_delay_risk.analytics import OperationalAnalytics, build_analytics


DATASET = Path(__file__).parents[1] / "data" / "operational_flights.csv"


@pytest.fixture
def analytics() -> OperationalAnalytics:
    return build_analytics(load_operational_csv(DATASET))


def test_analytics_store_loads_validated_records(analytics: OperationalAnalytics) -> None:
    assert analytics.total_flights() == 22
    assert list(analytics.to_dataframe().columns) == [
        "flight_id", "scheduled_departure", "delay_minutes", "weather_risk",
        "crew_issue", "risk_category",
    ]


def test_sql_risk_distribution_and_average_delay(analytics: OperationalAnalytics) -> None:
    assert analytics.risk_counts() == {"LOW": 5, "MEDIUM": 9, "HIGH": 8}
    assert analytics.average_delay() == pytest.approx(58.86363636)


@pytest.mark.parametrize(
    ("threshold", "expected"), [(30, 17), (60, 11), (120, 2)]
)
def test_sql_delay_thresholds(
    analytics: OperationalAnalytics, threshold: int, expected: int
) -> None:
    assert analytics.threshold_count(threshold) == expected


def test_sql_operational_conditions(analytics: OperationalAnalytics) -> None:
    assert analytics.weather_risk_count() == 10
    assert analytics.crew_issue_count() == 11
    assert analytics.combined_weather_crew_count() == 6
    assert analytics.condition_counts() == {
        "neither": 7, "weather_only": 4, "crew_only": 5, "both": 6
    }


def test_high_risk_extraction_is_deterministic(analytics: OperationalAnalytics) -> None:
    flights = analytics.high_risk_flights()
    assert len(flights) == 8
    assert [flight["flight_id"] for flight in flights] == [
        "FL008", "FL009", "FL011", "FL012", "FL017", "FL018", "FL019", "FL022"
    ]
    assert all(flight["risk_category"] == "HIGH" for flight in flights)


def test_kpi_summary_counts_rates_and_median(analytics: OperationalAnalytics) -> None:
    summary = analytics.kpi_summary()
    assert summary["total_flights"] == 22
    assert summary["average_delay_minutes"] == 58.86
    assert summary["median_delay_minutes"] == 59.5
    assert summary["delayed_ge_30_count"] == 17
    assert summary["delayed_ge_30_rate"] == 0.7727
    assert summary["severe_delay_ge_60_count"] == 11
    assert summary["extreme_delay_ge_120_count"] == 2
    assert summary["low_count"] == 5
    assert summary["medium_count"] == 9
    assert summary["high_count"] == 8
    assert summary["weather_risk_count"] == 10
    assert summary["crew_issue_count"] == 11


def test_pandas_distributions_and_condition_rates(analytics: OperationalAnalytics) -> None:
    risk = analytics.risk_distribution()
    conditions = analytics.operational_condition_distribution()
    assert list(risk["category"]) == ["LOW", "MEDIUM", "HIGH"]
    assert list(risk["count"]) == [5, 9, 8]
    assert conditions["rate"].sum() == pytest.approx(1.0)


def test_pandas_daily_and_hourly_departure_grouping(
    analytics: OperationalAnalytics,
) -> None:
    daily = analytics.departures_by_day()
    hourly = analytics.departures_by_hour()
    assert daily.to_dict("records") == [
        {"scheduled_date": "2026-01-05", "flight_count": 13},
        {"scheduled_date": "2026-01-06", "flight_count": 9},
    ]
    assert hourly.iloc[0].to_dict() == {"scheduled_hour": 6, "flight_count": 2}
    assert int(hourly["flight_count"].sum()) == 22


def test_high_risk_dataframe_is_analysis_ready(analytics: OperationalAnalytics) -> None:
    frame = analytics.high_risk_dataframe()
    assert isinstance(frame, pd.DataFrame)
    assert len(frame) == 8
    assert set(frame["risk_category"]) == {"HIGH"}


def test_empty_input_is_deterministic() -> None:
    analytics = OperationalAnalytics()
    assert analytics.total_flights() == 0
    assert analytics.average_delay() == 0.0
    assert analytics.kpi_summary()["median_delay_minutes"] == 0.0
    assert analytics.risk_counts() == {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
    assert list(analytics.departures_by_day().columns) == [
        "scheduled_date", "flight_count"
    ]


def test_non_validated_records_are_rejected() -> None:
    with pytest.raises(TypeError):
        OperationalAnalytics([object()])


def test_repeatability(analytics: OperationalAnalytics) -> None:
    first = analytics.kpi_summary()
    second = build_analytics(load_operational_csv(DATASET)).kpi_summary()
    assert first == second

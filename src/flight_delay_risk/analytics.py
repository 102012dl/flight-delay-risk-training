"""SQLite and pandas analytics for validated operational flight records."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from typing import Any

import pandas as pd

from .operational_data import FlightOperationalRecord


CONDITION_ORDER = ("neither", "weather_only", "crew_only", "both")
RISK_ORDER = ("LOW", "MEDIUM", "HIGH")
RATE_DECIMAL_PLACES = 4


class OperationalAnalytics:
    """Deterministic analytical facade over validated flight records.

    The existing CSV loader and classifier are intentionally outside this
    class.  Callers must provide ``FlightOperationalRecord`` instances, so
    W2D1 remains the validation boundary and the record's classifier remains
    the single source of truth for ``risk_category``.
    """

    def __init__(self, records: Iterable[FlightOperationalRecord] = ()) -> None:
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        self._create_schema()
        self.load_records(records)

    def __enter__(self) -> OperationalAnalytics:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        self.connection.close()

    def _create_schema(self) -> None:
        self.connection.execute(
            """
            CREATE TABLE flights (
                flight_id TEXT PRIMARY KEY,
                scheduled_departure TEXT NOT NULL,
                delay_minutes INTEGER NOT NULL,
                weather_risk INTEGER NOT NULL,
                crew_issue INTEGER NOT NULL,
                risk_category TEXT NOT NULL
            )
            """
        )
        self.connection.commit()

    def load_records(self, records: Iterable[FlightOperationalRecord]) -> int:
        """Insert validated records and return the number inserted."""
        rows = []
        for record in records:
            if not isinstance(record, FlightOperationalRecord):
                raise TypeError("records must contain FlightOperationalRecord values")
            rows.append(
                (
                    record.flight_id,
                    record.scheduled_departure.isoformat(),
                    record.delay_minutes,
                    int(record.weather_risk),
                    int(record.crew_issue),
                    record.risk_category,
                )
            )
        self.connection.executemany(
            """
            INSERT INTO flights (
                flight_id, scheduled_departure, delay_minutes, weather_risk,
                crew_issue, risk_category
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        self.connection.commit()
        return len(rows)

    def _scalar(self, query: str, parameters: tuple[Any, ...] = ()) -> Any:
        return self.connection.execute(query, parameters).fetchone()[0]

    def total_flights(self) -> int:
        return int(self._scalar("SELECT COUNT(*) FROM flights"))

    def average_delay(self) -> float:
        value = self._scalar("SELECT AVG(delay_minutes) FROM flights")
        return 0.0 if value is None else float(value)

    def risk_counts(self) -> dict[str, int]:
        rows = self.connection.execute(
            "SELECT risk_category, COUNT(*) AS count FROM flights "
            "GROUP BY risk_category"
        ).fetchall()
        counts = {risk: 0 for risk in RISK_ORDER}
        counts.update({row["risk_category"]: int(row["count"]) for row in rows})
        return counts

    def threshold_count(self, minimum_delay: int) -> int:
        return int(
            self._scalar(
                "SELECT COUNT(*) FROM flights WHERE delay_minutes >= ?",
                (minimum_delay,),
            )
        )

    def weather_risk_count(self) -> int:
        return int(self._scalar("SELECT COUNT(*) FROM flights WHERE weather_risk = 1"))

    def crew_issue_count(self) -> int:
        return int(self._scalar("SELECT COUNT(*) FROM flights WHERE crew_issue = 1"))

    def combined_weather_crew_count(self) -> int:
        return int(
            self._scalar(
                "SELECT COUNT(*) FROM flights WHERE weather_risk = 1 AND crew_issue = 1"
            )
        )

    def condition_counts(self) -> dict[str, int]:
        rows = self.connection.execute(
            """
            SELECT CASE
                WHEN weather_risk = 1 AND crew_issue = 1 THEN 'both'
                WHEN weather_risk = 1 THEN 'weather_only'
                WHEN crew_issue = 1 THEN 'crew_only'
                ELSE 'neither'
            END AS condition, COUNT(*) AS count
            FROM flights
            GROUP BY condition
            """
        ).fetchall()
        counts = {condition: 0 for condition in CONDITION_ORDER}
        counts.update({row["condition"]: int(row["count"]) for row in rows})
        return counts

    def high_risk_flights(self) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            """
            SELECT flight_id, scheduled_departure, delay_minutes,
                   weather_risk, crew_issue, risk_category
            FROM flights
            WHERE risk_category = ?
            ORDER BY scheduled_departure, flight_id
            """,
            ("HIGH",),
        ).fetchall()
        return [dict(row) for row in rows]

    def to_dataframe(self) -> pd.DataFrame:
        rows = self.connection.execute(
            """
            SELECT flight_id, scheduled_departure, delay_minutes,
                   weather_risk, crew_issue, risk_category
            FROM flights
            ORDER BY scheduled_departure, flight_id
            """
        ).fetchall()
        columns = [
            "flight_id", "scheduled_departure", "delay_minutes", "weather_risk",
            "crew_issue", "risk_category",
        ]
        frame = pd.DataFrame([dict(row) for row in rows], columns=columns)
        if not frame.empty:
            frame["scheduled_departure"] = pd.to_datetime(
                frame["scheduled_departure"], utc=True
            )
            frame["weather_risk"] = frame["weather_risk"].astype(bool)
            frame["crew_issue"] = frame["crew_issue"].astype(bool)
        return frame

    def risk_distribution(self) -> pd.DataFrame:
        return self._distribution_frame("risk_category", RISK_ORDER)

    def delay_threshold_distribution(self) -> pd.DataFrame:
        total = self.total_flights()
        rows = [
            {"threshold": f">={threshold}", "count": self.threshold_count(threshold)}
            for threshold in (30, 60, 120)
        ]
        frame = pd.DataFrame(rows, columns=["threshold", "count"])
        frame["rate"] = frame["count"].map(lambda count: self._rate(count, total))
        return frame

    def operational_condition_distribution(self) -> pd.DataFrame:
        counts = self.condition_counts()
        total = self.total_flights()
        return pd.DataFrame(
            [
                {"condition": condition, "count": counts[condition],
                 "rate": self._rate(counts[condition], total)}
                for condition in CONDITION_ORDER
            ]
        )

    def departures_by_day(self) -> pd.DataFrame:
        frame = self.to_dataframe()
        if frame.empty:
            return pd.DataFrame(columns=["scheduled_date", "flight_count"])
        result = (
            frame.assign(scheduled_date=frame["scheduled_departure"].dt.strftime("%Y-%m-%d"))
            .groupby("scheduled_date", as_index=False)
            .size()
            .rename(columns={"size": "flight_count"})
        )
        return result.sort_values("scheduled_date").reset_index(drop=True)

    def departures_by_hour(self) -> pd.DataFrame:
        frame = self.to_dataframe()
        if frame.empty:
            return pd.DataFrame(columns=["scheduled_hour", "flight_count"])
        return (
            frame.assign(scheduled_hour=frame["scheduled_departure"].dt.hour)
            .groupby("scheduled_hour", as_index=False)
            .size()
            .rename(columns={"size": "flight_count"})
            .sort_values("scheduled_hour")
            .reset_index(drop=True)
        )

    def high_risk_dataframe(self) -> pd.DataFrame:
        return self.to_dataframe().query("risk_category == 'HIGH'").reset_index(drop=True)

    def kpi_summary(self) -> dict[str, int | float]:
        total = self.total_flights()
        risk_counts = self.risk_counts()
        summary: dict[str, int | float] = {
            "total_flights": total,
            "average_delay_minutes": round(self.average_delay(), 2),
            "median_delay_minutes": self._median_delay(),
        }
        for threshold, name in ((30, "delayed_ge_30"), (60, "severe_delay_ge_60"),
                                (120, "extreme_delay_ge_120")):
            count = self.threshold_count(threshold)
            summary[f"{name}_count"] = count
            summary[f"{name}_rate"] = self._rate(count, total)
        for risk in RISK_ORDER:
            summary[f"{risk.lower()}_count"] = risk_counts[risk]
            summary[f"{risk.lower()}_rate"] = self._rate(risk_counts[risk], total)
        weather = self.weather_risk_count()
        crew = self.crew_issue_count()
        summary["weather_risk_count"] = weather
        summary["weather_risk_rate"] = self._rate(weather, total)
        summary["crew_issue_count"] = crew
        summary["crew_issue_rate"] = self._rate(crew, total)
        return summary

    def _median_delay(self) -> float:
        values = self.to_dataframe()["delay_minutes"]
        median = values.median()
        return 0.0 if pd.isna(median) else float(median)

    def _distribution_frame(self, column: str, order: tuple[str, ...]) -> pd.DataFrame:
        counts = self.to_dataframe()[column].value_counts().to_dict()
        total = self.total_flights()
        return pd.DataFrame(
            [{"category": value, "count": int(counts.get(value, 0)),
              "rate": self._rate(int(counts.get(value, 0)), total)} for value in order]
        )

    @staticmethod
    def _rate(count: int, total: int) -> float:
        return round(count / total, RATE_DECIMAL_PLACES) if total else 0.0


def build_analytics(records: Iterable[FlightOperationalRecord]) -> OperationalAnalytics:
    """Build an in-memory analytics store from validated records."""
    return OperationalAnalytics(records)

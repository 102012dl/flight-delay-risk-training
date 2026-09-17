"""Leakage-controlled, synthetic predictive baseline for severe delays."""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split


FEATURE_COLUMNS = ("weather_risk", "crew_issue", "departure_hour")
TARGET_COLUMN = "severe_delay"
FORBIDDEN_FEATURE_COLUMNS = ("delay_minutes", "risk_category", "flight_id")


@dataclass(frozen=True)
class TrainTestSplit:
    """Prepared, disjoint training and test partitions with IDs for auditing."""

    X_train: pd.DataFrame
    X_test: pd.DataFrame
    y_train: pd.Series
    y_test: pd.Series
    train_ids: pd.Series
    test_ids: pd.Series


@dataclass(frozen=True)
class EvaluationMetrics:
    """Held-out classification metrics for the positive severe-delay class."""

    recall: float
    precision: float
    f1: float
    balanced_accuracy: float
    confusion_matrix: tuple[tuple[int, int], tuple[int, int]]


def generate_synthetic_training_frame(
    n_records: int = 240, random_state: int = 42
) -> pd.DataFrame:
    """Generate deterministic, noisy aviation records for educational training."""
    if n_records <= 0:
        raise ValueError("n_records must be greater than zero")

    rng = random.Random(random_state)
    start = datetime(2025, 1, 6, 5, 0)
    rows: list[dict[str, Any]] = []
    for index in range(n_records):
        departure = start + timedelta(hours=index % 24, days=index // 24)
        weather_risk = rng.random() < 0.24
        crew_issue = rng.random() < 0.12
        peak_hour = departure.hour in {7, 8, 16, 17, 18}
        severe_probability = 0.10 + 0.18 * weather_risk + 0.14 * crew_issue
        severe_probability += 0.04 * peak_hour
        is_severe = rng.random() < severe_probability
        if is_severe:
            delay = max(60, round(rng.gauss(88, 22)))
        else:
            delay = min(59, max(0, round(rng.gauss(14, 12))))
        rows.append(
            {
                "flight_id": f"SYN-{index + 1:04d}",
                "scheduled_departure": departure,
                "delay_minutes": int(delay),
                "weather_risk": weather_risk,
                "crew_issue": crew_issue,
            }
        )

    frame = pd.DataFrame(rows)
    frame["risk_category"] = frame.apply(
        lambda row: "HIGH" if row.delay_minutes >= 60 else "LOW", axis=1
    )
    frame[TARGET_COLUMN] = frame["delay_minutes"] >= 60
    return frame


def prepare_features(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Return only prediction-time-valid features and the explicit target."""
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        raise ValueError("frame must be a non-empty pandas DataFrame")
    required = {
        "flight_id", "scheduled_departure", "delay_minutes", "weather_risk", "crew_issue"
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"frame is missing required columns: {', '.join(missing)}")
    X = pd.DataFrame(index=frame.index)
    X["weather_risk"] = frame["weather_risk"].astype(int)
    X["crew_issue"] = frame["crew_issue"].astype(int)
    X["departure_hour"] = pd.to_datetime(frame["scheduled_departure"]).dt.hour
    y = (frame["delay_minutes"] >= 60).astype(int).rename(TARGET_COLUMN)
    return X.loc[:, FEATURE_COLUMNS], y


def split_features(frame: pd.DataFrame, random_state: int = 42) -> TrainTestSplit:
    """Prepare and reproducibly split records without fitting on test data."""
    X, y = prepare_features(frame)
    ids = frame["flight_id"].copy()
    stratify = y if y.nunique() == 2 and y.value_counts().min() >= 2 else None
    train_idx, test_idx = train_test_split(
        frame.index, test_size=0.2, random_state=random_state, stratify=stratify
    )
    return TrainTestSplit(
        X.loc[train_idx], X.loc[test_idx], y.loc[train_idx], y.loc[test_idx],
        ids.loc[train_idx], ids.loc[test_idx]
    )


def train_dummy_classifier(split: TrainTestSplit) -> DummyClassifier:
    """Fit the prior-only naïve benchmark on the training partition."""
    model = DummyClassifier(strategy="prior")
    return model.fit(split.X_train, split.y_train)


def train_logistic_regression(split: TrainTestSplit) -> LogisticRegression:
    """Fit a minimal, interpretable, reproducible baseline classifier."""
    model = LogisticRegression(
        random_state=42, max_iter=1000, class_weight="balanced"
    )
    return model.fit(split.X_train, split.y_train)


def evaluate_model(model: Any, split: TrainTestSplit) -> EvaluationMetrics:
    """Evaluate a fitted model on held-out data with an explicit metric contract."""
    predictions = model.predict(split.X_test)
    matrix = confusion_matrix(split.y_test, predictions, labels=[0, 1])
    return EvaluationMetrics(
        recall=float(recall_score(split.y_test, predictions, zero_division=0)),
        precision=float(precision_score(split.y_test, predictions, zero_division=0)),
        f1=float(f1_score(split.y_test, predictions, zero_division=0)),
        balanced_accuracy=float(balanced_accuracy_score(split.y_test, predictions)),
        confusion_matrix=(
            tuple(int(value) for value in matrix[0]),
            tuple(int(value) for value in matrix[1]),
        ),
    )


def logistic_coefficients(model: LogisticRegression) -> dict[str, float]:
    """Expose feature associations for inspection; these are not causal effects."""
    if not hasattr(model, "coef_"):
        raise ValueError("model must be a fitted LogisticRegression")
    return dict(zip(FEATURE_COLUMNS, model.coef_[0], strict=True))

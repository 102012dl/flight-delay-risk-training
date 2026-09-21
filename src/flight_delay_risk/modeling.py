"""Leakage-controlled, synthetic predictive baseline for severe delays."""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from math import exp
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


@dataclass(frozen=True)
class EvaluationRow:
    """One post-hoc, auditable prediction result from the test partition."""

    flight_id: str
    weather_risk: bool
    crew_issue: bool
    departure_hour: int
    actual_target: int
    predicted_target: int
    error_class: str


@dataclass(frozen=True)
class ThresholdEvaluation:
    """Metrics for one predefined educational probability threshold."""

    threshold: float
    metrics: EvaluationMetrics


@dataclass(frozen=True)
class FeatureExplanation:
    """Non-causal interpretation of one fitted logistic coefficient."""

    feature: str
    coefficient: float
    direction: str
    odds_ratio: float


ERROR_CLASS_INTERPRETATIONS = {
    "TN": "correct non-severe prediction",
    "FP": "non-severe case incorrectly flagged",
    "FN": "severe-delay case missed",
    "TP": "severe-delay case correctly flagged",
}

EDUCATIONAL_THRESHOLDS = (0.30, 0.50, 0.70)

LIMITATIONS = {
    "data": "synthetic data only",
    "generator_risk": "MEDIUM",
    "generalization": "MEDIUM / not established on real data",
    "causality": "no causal interpretation",
    "deployment": "no airline deployment claim",
    "threshold": "no calibrated operational threshold",
    "cost": "no monetary impact estimate",
    "monitoring": "no production monitoring",
    "validation": "no real-airline validation",
    "automation": "not approved for autonomous operational action",
}


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
    return _metrics_from_predictions(split.y_test, predictions)


def _metrics_from_predictions(
    actual: pd.Series, predictions: Any
) -> EvaluationMetrics:
    """Build the existing metric contract from already-generated predictions."""
    matrix = confusion_matrix(actual, predictions, labels=[0, 1])
    return EvaluationMetrics(
        recall=float(recall_score(actual, predictions, zero_division=0)),
        precision=float(precision_score(actual, predictions, zero_division=0)),
        f1=float(f1_score(actual, predictions, zero_division=0)),
        balanced_accuracy=float(balanced_accuracy_score(actual, predictions)),
        confusion_matrix=(
            tuple(int(value) for value in matrix[0]),
            tuple(int(value) for value in matrix[1]),
        ),
    )


def _error_class(actual: int, predicted: int) -> str:
    """Return the standard confusion-matrix label for one prediction."""
    return {(0, 0): "TN", (0, 1): "FP", (1, 0): "FN", (1, 1): "TP"}[
        (int(actual), int(predicted))
    ]


def build_evaluation_rows(
    model: Any, split: TrainTestSplit, frame: pd.DataFrame
) -> tuple[EvaluationRow, ...]:
    """Build post-hoc audit rows without changing the model feature matrix."""
    required = {"flight_id", "weather_risk", "crew_issue", "scheduled_departure"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"frame is missing required columns: {', '.join(missing)}")
    predictions = model.predict(split.X_test)
    source = frame.loc[split.test_ids.index]
    return tuple(
        EvaluationRow(
            flight_id=str(row.flight_id),
            weather_risk=bool(row.weather_risk),
            crew_issue=bool(row.crew_issue),
            departure_hour=int(pd.to_datetime(row.scheduled_departure).hour),
            actual_target=int(actual),
            predicted_target=int(predicted),
            error_class=_error_class(actual, predicted),
        )
        for (_, row), actual, predicted in zip(
            source.iterrows(), split.y_test, predictions, strict=True
        )
    )


def filter_evaluation_rows(
    rows: tuple[EvaluationRow, ...], error_class: str
) -> tuple[EvaluationRow, ...]:
    """Return rows for one TN/FP/FN/TP class."""
    if error_class not in ERROR_CLASS_INTERPRETATIONS:
        raise ValueError("error_class must be one of TN, FP, FN, or TP")
    return tuple(row for row in rows if row.error_class == error_class)


def evaluate_fixed_thresholds(
    model: LogisticRegression,
    split: TrainTestSplit,
    thresholds: tuple[float, ...] = EDUCATIONAL_THRESHOLDS,
) -> tuple[ThresholdEvaluation, ...]:
    """Evaluate predefined thresholds without selecting or optimizing one."""
    if thresholds != EDUCATIONAL_THRESHOLDS:
        raise ValueError("thresholds must remain the approved fixed educational set")
    probabilities = model.predict_proba(split.X_test)[:, 1]
    return tuple(
        ThresholdEvaluation(
            threshold=threshold,
            metrics=_metrics_from_predictions(
                split.y_test, (probabilities >= threshold).astype(int)
            ),
        )
        for threshold in thresholds
    )


def explain_logistic_model(model: LogisticRegression) -> tuple[FeatureExplanation, ...]:
    """Expose fitted associations, not causal effects or probabilities."""
    coefficients = logistic_coefficients(model)
    return tuple(
        FeatureExplanation(
            feature=feature,
            coefficient=float(coefficient),
            direction="positive" if coefficient > 0 else "negative",
            odds_ratio=float(exp(coefficient)),
        )
        for feature, coefficient in coefficients.items()
    )


def limitations_metadata() -> dict[str, str]:
    """Return the explicit non-production governance contract."""
    return dict(LIMITATIONS)


def logistic_coefficients(model: LogisticRegression) -> dict[str, float]:
    """Expose feature associations for inspection; these are not causal effects."""
    if not hasattr(model, "coef_"):
        raise ValueError("model must be a fitted LogisticRegression")
    return dict(zip(FEATURE_COLUMNS, model.coef_[0], strict=True))

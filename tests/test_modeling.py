import pandas as pd
import pytest

from flight_delay_risk.modeling import (
    FEATURE_COLUMNS,
    EvaluationMetrics,
    evaluate_model,
    generate_synthetic_training_frame,
    logistic_coefficients,
    prepare_features,
    split_features,
    train_dummy_classifier,
    train_logistic_regression,
)


def test_generation_is_deterministic_and_has_unique_ids_and_both_classes():
    frame = generate_synthetic_training_frame()
    assert frame.equals(generate_synthetic_training_frame())
    assert len(frame) == 240
    assert frame.flight_id.is_unique
    assert frame.severe_delay.nunique() == 2


def test_target_is_derived_from_outcome():
    frame = generate_synthetic_training_frame()
    assert (frame.severe_delay == (frame.delay_minutes >= 60)).all()


def test_feature_contract_excludes_forbidden_fields():
    frame = generate_synthetic_training_frame()
    X, y = prepare_features(frame)
    assert list(X.columns) == list(FEATURE_COLUMNS)
    assert set(X.columns).isdisjoint({"delay_minutes", "risk_category", "flight_id"})
    assert y.name == "severe_delay"


def test_empty_or_missing_input_is_rejected():
    with pytest.raises(ValueError):
        prepare_features(pd.DataFrame())
    with pytest.raises(ValueError, match="scheduled_departure"):
        prepare_features(generate_synthetic_training_frame().drop(columns="scheduled_departure"))


def test_split_is_reproducible_and_ids_do_not_overlap():
    frame = generate_synthetic_training_frame()
    first = split_features(frame)
    second = split_features(frame)
    assert first.X_train.equals(second.X_train)
    assert first.test_ids.equals(second.test_ids)
    assert set(first.train_ids).isdisjoint(first.test_ids)


@pytest.mark.parametrize("trainer", [train_dummy_classifier, train_logistic_regression])
def test_models_train_and_evaluate_with_required_metrics(trainer):
    split = split_features(generate_synthetic_training_frame())
    metrics = evaluate_model(trainer(split), split)
    assert isinstance(metrics, EvaluationMetrics)
    assert 0 <= metrics.recall <= 1
    assert 0 <= metrics.precision <= 1
    assert 0 <= metrics.f1 <= 1
    assert 0 <= metrics.balanced_accuracy <= 1
    assert len(metrics.confusion_matrix) == 2
    assert all(len(row) == 2 for row in metrics.confusion_matrix)


def test_logistic_coefficients_match_approved_features():
    split = split_features(generate_synthetic_training_frame())
    coefficients = logistic_coefficients(train_logistic_regression(split))
    assert list(coefficients) == list(FEATURE_COLUMNS)

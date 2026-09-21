import pandas as pd
import pytest

from flight_delay_risk.modeling import (
    EDUCATIONAL_THRESHOLDS,
    FEATURE_COLUMNS,
    EvaluationMetrics,
    build_evaluation_rows,
    evaluate_fixed_thresholds,
    evaluate_model,
    explain_logistic_model,
    filter_evaluation_rows,
    generate_synthetic_training_frame,
    logistic_coefficients,
    prepare_features,
    split_features,
    train_dummy_classifier,
    train_logistic_regression,
    limitations_metadata,
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


def test_evaluation_rows_classify_all_confusion_matrix_cases():
    frame = generate_synthetic_training_frame()
    split = split_features(frame)
    rows = build_evaluation_rows(train_logistic_regression(split), split, frame)
    expected = {(0, 0): "TN", (0, 1): "FP", (1, 0): "FN", (1, 1): "TP"}
    assert {row.error_class for row in rows} == set(expected.values())
    assert all(expected[(row.actual_target, row.predicted_target)] == row.error_class for row in rows)


def test_false_positive_and_false_negative_extraction_is_deterministic():
    frame = generate_synthetic_training_frame()
    split = split_features(frame)
    rows = build_evaluation_rows(train_logistic_regression(split), split, frame)
    assert len(filter_evaluation_rows(rows, "FP")) == 14
    assert len(filter_evaluation_rows(rows, "FN")) == 3


def test_evaluation_rows_contain_approved_audit_information():
    frame = generate_synthetic_training_frame()
    split = split_features(frame)
    row = build_evaluation_rows(train_logistic_regression(split), split, frame)[0]
    assert row.flight_id
    assert row.departure_hour in range(24)
    assert set(row.__dataclass_fields__) == {
        "flight_id", "weather_risk", "crew_issue", "departure_hour",
        "actual_target", "predicted_target", "error_class",
    }


def test_evaluation_preserves_exact_leakage_safe_feature_contract():
    frame = generate_synthetic_training_frame()
    split = split_features(frame)
    assert list(split.X_train.columns) == list(FEATURE_COLUMNS)
    assert set(split.X_train.columns).isdisjoint(
        {"delay_minutes", "risk_category", "flight_id", "actual_target", "predicted_target", "error_class"}
    )
    build_evaluation_rows(train_logistic_regression(split), split, frame)


def test_fixed_thresholds_are_predefined_and_reproducible():
    split = split_features(generate_synthetic_training_frame())
    model = train_logistic_regression(split)
    first = evaluate_fixed_thresholds(model, split)
    second = evaluate_fixed_thresholds(model, split)
    assert tuple(result.threshold for result in first) == EDUCATIONAL_THRESHOLDS
    assert first == second
    assert first[0].metrics.recall == pytest.approx(0.8571428571)
    assert first[1].metrics.confusion_matrix == ((27, 14), (3, 4))


def test_threshold_set_cannot_be_optimized_or_changed():
    split = split_features(generate_synthetic_training_frame())
    with pytest.raises(ValueError):
        evaluate_fixed_thresholds(train_logistic_regression(split), split, (0.5,))


def test_explainability_contains_coefficients_directions_and_odds_ratios():
    split = split_features(generate_synthetic_training_frame())
    explanations = explain_logistic_model(train_logistic_regression(split))
    assert tuple(item.feature for item in explanations) == FEATURE_COLUMNS
    assert explanations[0].coefficient == pytest.approx(1.1022, abs=1e-4)
    assert explanations[0].direction == "positive"
    assert explanations[0].odds_ratio == pytest.approx(3.0109, abs=1e-3)


def test_limitations_metadata_exposes_non_production_boundaries():
    limitations = limitations_metadata()
    assert limitations["data"] == "synthetic data only"
    assert limitations["generator_risk"] == "MEDIUM"
    assert limitations["generalization"] == "MEDIUM / not established on real data"
    assert limitations["automation"] == "not approved for autonomous operational action"

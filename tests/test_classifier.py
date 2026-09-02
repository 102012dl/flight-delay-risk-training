import pytest

from flight_delay_risk import classify_delay_risk


def test_t_01_zero_delay_without_risks_is_low() -> None:
    assert classify_delay_risk(0, False, False) == "LOW"


def test_t_02_delay_under_30_with_risks_is_low() -> None:
    assert classify_delay_risk(29, True, True) == "LOW"


def test_t_03_delay_at_30_without_risks_is_medium() -> None:
    assert classify_delay_risk(30, False, False) == "MEDIUM"


def test_t_04_delay_under_60_with_risks_is_medium() -> None:
    assert classify_delay_risk(59, True, True) == "MEDIUM"


def test_t_05_delay_at_120_without_risks_is_high() -> None:
    assert classify_delay_risk(120, False, False) == "HIGH"


def test_t_06_negative_delay_raises_value_error() -> None:
    with pytest.raises(ValueError):
        classify_delay_risk(-1, False, False)


def test_t_07_delay_at_60_with_weather_risk_is_high() -> None:
    assert classify_delay_risk(60, True, False) == "HIGH"


def test_t_08_delay_at_60_with_crew_issue_is_high() -> None:
    assert classify_delay_risk(60, False, True) == "HIGH"


def test_t_09_delay_at_60_without_risks_is_medium():
    assert classify_delay_risk(60, False, False) == "MEDIUM"


def test_t_10_non_integer_delay_raises_type_error() -> None:
    with pytest.raises(TypeError):
        classify_delay_risk("60", False, False)


def test_t_11_boolean_delay_raises_type_error() -> None:
    with pytest.raises(TypeError):
        classify_delay_risk(True, False, False)


def test_t_12_non_boolean_weather_risk_raises_type_error() -> None:
    with pytest.raises(TypeError):
        classify_delay_risk(60, "yes", False)


def test_t_13_non_boolean_crew_issue_raises_type_error() -> None:
    with pytest.raises(TypeError):
        classify_delay_risk(60, False, 1)


def test_t_14_delay_at_119_without_risks_is_medium() -> None:
    assert classify_delay_risk(119, False, False) == "MEDIUM"


def test_t_15_delay_at_59_with_weather_risk_is_medium() -> None:
    assert classify_delay_risk(59, True, False) == "MEDIUM"


def test_t_16_delay_at_59_with_crew_issue_is_medium() -> None:
    assert classify_delay_risk(59, False, True) == "MEDIUM"

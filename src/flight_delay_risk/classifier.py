"""Deterministic flight delay risk classification."""


def classify_delay_risk(
    delay_minutes: int,
    weather_risk: bool,
    crew_issue: bool,
) -> str:
    """Classify flight delay risk as LOW, MEDIUM, or HIGH."""
    if not isinstance(delay_minutes, int) or isinstance(delay_minutes, bool):
        raise TypeError
    if not isinstance(weather_risk, bool):
        raise TypeError
    if not isinstance(crew_issue, bool):
        raise TypeError

    if delay_minutes < 0:
        raise ValueError

    if (
        delay_minutes >= 120
        or (delay_minutes >= 60 and weather_risk)
        or (delay_minutes >= 60 and crew_issue)
    ):
        return "HIGH"

    if delay_minutes >= 30:
        return "MEDIUM"

    return "LOW"

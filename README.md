# Flight Delay Risk Training

## Objective

Provide a small deterministic classifier for flight delay risk based on delay
duration and two operational risk flags.

## Controlled Training Application

This project is a controlled software-engineering training application. It is
intended to demonstrate a typed, deterministic, rule-based Python function with
local pytest coverage.

## Inputs

- `delay_minutes: int`
- `weather_risk: bool`
- `crew_issue: bool`

## Outputs

- `LOW`
- `MEDIUM`
- `HIGH`

## Rules

Rules are evaluated in this exact order:

1. Negative delay raises `ValueError`.
2. `HIGH` for delay `>= 120`.
3. `HIGH` for delay `>= 60` with `weather_risk` true.
4. `HIGH` for delay `>= 60` with `crew_issue` true.
5. Otherwise `MEDIUM` for delay `>= 30`.
6. Otherwise `LOW`.

## Usage

```python
from flight_delay_risk import classify_delay_risk

risk = classify_delay_risk(60, weather_risk=True, crew_issue=False)
```

## Test

```powershell
python -m pytest -v
```

## Limitations

- Deterministic rule-based classifier.
- No API, UI, database, persistence, external services, or deployment.
- Created only for controlled software-engineering training.

## Aviation Operational Data Foundation

This increment adds a small, reproducible operational-data layer:

```text
Synthetic Operational CSV
        ↓
Data Contract
        ↓
Validation
        ↓
Risk Classifier
        ↓
Analysis-ready Output
```

The dataset at `data/operational_flights.csv` is **SYNTHETIC TRAINING DATA**
and **NOT REAL AIRLINE OPERATIONAL DATA**. It contains no real airline,
customer, personal, or proprietary data and makes no production operational
claim.

`flight_delay_risk.operational_data` validates required fields, parses strict
CSV values into `FlightOperationalRecord`, rejects unsafe records explicitly,
and passes valid records to the existing Week-1 classifier.

## Market-aligned competencies

- Direct evidence: Python data processing, structured operational records,
  data-quality validation, aviation delay/weather/crew risk logic, focused
  automated tests, and Git/evidence discipline.
- Partial evidence: SQL/pandas readiness through a typed tabular contract and
  analysis-ready records; neither SQL nor pandas is implemented yet.
- Not implemented: machine learning, deployment, APIs, dashboards, and
  MLOps.

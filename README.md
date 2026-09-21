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

## W2D3 Leakage-controlled predictive baseline

W2D3 adds a small educational predictive benchmark using deterministically
generated synthetic aviation operational data (seed `42`, approximately 240
records). The target is `severe_delay`, defined explicitly as
`delay_minutes >= 60`. At prediction time, the model uses only `weather_risk`,
`crew_issue`, and a derived `departure_hour`; `flight_id`, `delay_minutes`, and
`risk_category` are excluded as identifiers or post-outcome fields.

The benchmark compares `DummyClassifier(strategy="prior")` with a minimal
`LogisticRegression`. Held-out evaluation reports recall as the primary metric
because missing a severe delay is operationally important, with precision, F1,
balanced accuracy, and a confusion matrix as supporting metrics. Logistic
coefficients expose associations within this synthetic dataset; they are not
causal effects.

This is a synthetic educational benchmark, not production-validated ML or a
real airline performance claim. It makes no business-impact or stable-
generalization claim. The existing deterministic rule engine and this
predictive model are separate artifacts: **RULE ENGINE != PREDICTIVE MODEL**.

## W2D2 Operational Analytics

W2D2 adds a small, deterministic analytics layer for the validated synthetic
records. The flow is:

```text
Validated FlightOperationalRecord
        ↓
Existing Week-1 classifier
        ↓
In-memory SQLite analytical table
        ↓
SQL queries and pandas DataFrames
        ↓
OCC-style KPI and EDA outputs
```

`flight_delay_risk.analytics.OperationalAnalytics` accepts only validated
`FlightOperationalRecord` values. It stores the already-derived
`risk_category` in SQLite and provides SQL-backed counts, averages, threshold
queries, operational-condition groups, and HIGH-risk extraction. pandas adds
median delay, KPI rates, risk and condition distributions, daily/hourly
departure grouping, and analysis-ready DataFrames.

Example:

```python
from flight_delay_risk import load_operational_csv
from flight_delay_risk.analytics import build_analytics

records = load_operational_csv("data/operational_flights.csv")
analytics = build_analytics(records)
print(analytics.kpi_summary())
print(analytics.departures_by_hour())
```

The outputs describe only fields present in this dataset: delay minutes,
scheduled departure, weather risk, crew issue, and derived risk category.
OTP, actual movement performance, cancellations, diversions, passenger or
financial impact, and network effects are not represented. This remains
**SYNTHETIC TRAINING DATA — NOT REAL AIRLINE OPERATIONAL DATA**; machine
learning, APIs, dashboards, deployment, and production airline readiness are
outside W2D2.

## W2D4 Evaluation and decision-support evidence

W2D4 asks: **What does the baseline model's behaviour mean for an aviation
operations decision-maker, where does it fail, and when should it not be
trusted?** The held-out logistic benchmark produces TN=27, FP=14, FN=3,
and TP=4: it detects 4 of 7 severe synthetic cases while generating 14
false alerts. A false negative is a severe-delay case missed by the model;
a false positive is a non-severe case incorrectly flagged. These support
human review and hypothetical decision-support analysis only, not autonomous
operational intervention or claims about real airline workload, cost, safety,
or passenger impact.

The fixed educational thresholds 0.30, 0.50, and 0.70 illustrate the
recall/false-positive trade-off. No threshold is operationally recommended:
real use would require real data, independent validation, calibrated
probabilities, explicit costs, stakeholder requirements, and risk tolerance.

Logistic coefficients describe fitted associations within this synthetic
model, not causal effects, real-airline estimates, or operational probability
guarantees. `departure_hour` is treated linearly and does not robustly model
cyclic time-of-day behaviour. Synthetic-generator bias and small-segment
overinterpretation remain material limitations. This is an educational,
decision-support training artifact with no real-airline validation, production
monitoring, or airline deployment claim. API/FastAPI, Docker, CI/CD, and
deployment-oriented work remain reserved for W3.

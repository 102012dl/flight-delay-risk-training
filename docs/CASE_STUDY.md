# Flight Delay Risk Training — Technical Case Study

## Business / operational problem

Aviation stakeholders need delay-risk evidence that is understandable,
testable, and bounded before it can inform a real workflow. This project
builds a small training system that makes the data contract, rule boundaries,
analytics, model errors, API behaviour, and governance limits inspectable.

## Context

The repository uses deterministic synthetic operational flight data. It is
designed to demonstrate engineering and analytical judgement, not to represent
an airline, certify safety, or predict real-world performance.

## Engineering / analytical decisions

- Preserved the authoritative rule engine and separated it from the predictive
  benchmark (`RULE ENGINE != PREDICTIVE MODEL`).
- Validated records before analytics and kept the operational schema explicit.
- Used a DummyClassifier baseline and minimal LogisticRegression benchmark.
- Excluded identifiers, delay outcome, and derived risk from model features to
  make the training split leakage-controlled.
- Treated recall as the primary educational lens while retaining precision,
  F1, balanced accuracy, and confusion-matrix evidence.
- Kept thresholds fixed and illustrative rather than pretending to optimize an
  operational policy.

## Architecture

`synthetic CSV → strict data contract → classifier → SQLite/pandas analytics`

and independently:

`synthetic generated frame → approved features → reproducible split → baseline
models → held-out evaluation and explanations`

FastAPI provides a typed local adapter over the existing classifier:
`JSON → strict Pydantic validation → /risk → domain function → typed response`.

## Data foundation

`operational_data.py` parses strict CSV values into structured records, rejects
invalid records and duplicate identifiers, and classifies valid records using
the existing domain function. The data is synthetic and contains no real
passenger, crew, or proprietary airline information.

## Analytics

The analytics layer uses in-memory SQLite and pandas for risk counts, average
and median delay, thresholds, operational-condition groups, daily/hourly
grouping, and high-risk extraction. It does not claim to measure OTP,
cancellations, diversions, passenger impact, financial impact, or network
effects.

## Baseline ML and model evaluation

The benchmark compares a prior DummyClassifier with LogisticRegression on
synthetic data generated with seed 42. The recorded logistic evaluation at the
documented 0.50 educational threshold is TN=27, FP=14, FN=3, TP=4: 4 of 7
severe synthetic cases were detected and 14 non-severe cases were flagged.
Fixed 0.30/0.50/0.70 thresholds show trade-offs only. Coefficients are
associations in this dataset, not causal effects or airline estimates.

## API / engineering layer

The FastAPI service exposes `GET /health` and `POST /risk`. Strict Pydantic
validation rejects malformed, missing, extra, negative, and incorrectly typed
inputs. The adapter is deterministic, delegates to the existing classifier,
and has no database, credentials, network dependency, or external side effect.

## Testing / CI / Docker

The repository contains focused classifier, data-quality, analytics, modeling,
and API tests. The accepted W3 baseline is 79 passed and 0 failures. CI runs
the suite on Python 3.13. Docker packages the local service for reproducible
training execution. These artifacts do not establish production deployment,
scalability, uptime, or security certification.

## Governance / security

The [governance package](GOVERNANCE.md) records intended/prohibited use, a
material risk register, evidence traceability, human oversight, security and
privacy boundaries, and future controls clearly marked not implemented.

## Verified results

- 79-test accepted W3 baseline: 0 failures.
- Classifier boundaries, data validation, analytics, leakage-safe feature
  contract, model evaluation, API strictness, determinism, CI definition, and
  Docker packaging are represented by repository artifacts.
- No production or real-airline metric is claimed.

## Limitations

Synthetic-generator bias, small-sample behaviour, generalization, calibration,
drift, causal interpretation, real airline validity, operational cost, and
production security are not established. Thresholds are not recommendations.
Human review would be mandatory for any real decision-support workflow.

## What I would do next with real data

Establish governance and privacy authority first; then obtain representative,
approved data; define outcomes and costs with operations stakeholders; perform
temporal and route-aware validation; calibrate and monitor the model; test
fairness and failure modes; secure the service; and run a controlled human
pilot before any operational authorization. Those steps are future work, not
present implementation.

## Skills demonstrated

Python, typed data contracts, aviation-domain reasoning, SQL/SQLite and pandas
analytics, scikit-learn baselines, leakage control, evaluation design,
FastAPI/Pydantic, pytest regression testing, CI, Docker packaging, governance,
security-aware documentation, technical risk management, and stakeholder
communication.

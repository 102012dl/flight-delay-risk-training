# Governance, Risk, Security, and Traceability

Status: W4 local implementation package. Evidence is bounded by the verified
repository at commit `7cc8ac9a53d01b2e0249e9effd8ad492879b514b`.

## System / Model Card

### Purpose and users

This is a controlled aviation delay-risk training system for engineers,
analysts, data/AI reviewers, aviation-operations learners, and governance
stakeholders. It demonstrates how a small operational-data workflow can be
validated, analyzed, evaluated, and exposed through a typed local API.

### Intended and prohibited use

Intended use is education, reproducible technical review, and hypothetical
decision-support analysis. The deterministic classifier and predictive
benchmark are separate artifacts. Neither is intended to dispatch aircraft,
reassign crews, issue passenger communications, set an airline operating
threshold, certify safety, or make an autonomous operational decision.

### Inputs and outputs

- Rule engine: non-negative `delay_minutes`, `weather_risk`, and `crew_issue`.
- Operational data: a strict CSV contract containing flight identifier,
  departure time, delay, and risk fields; the supplied dataset is synthetic.
- Baseline model: `weather_risk`, `crew_issue`, and derived `departure_hour`;
  identifiers, delay outcome, and derived risk category are excluded from
  model features to reduce leakage.
- Outputs: `LOW`/`MEDIUM`/`HIGH` rule category, validated records, analytics,
  evaluation metrics, and a typed `/risk` API response.

### System boundary and roles

The flow is `synthetic CSV → validation → rule classification → SQLite/pandas
analytics`, alongside `synthetic generated frame → leakage-controlled split →
DummyClassifier and LogisticRegression evaluation`. FastAPI adapts the existing
rule function; it does not train a model or create an external side effect.

### Evaluation evidence

The baseline model uses deterministic seed 42 and held-out evaluation. The
recorded logistic evaluation has TN=27, FP=14, FN=3, TP=4 at the documented
educational 0.50 threshold and detects 4 of 7 severe synthetic cases. Fixed
0.30/0.50/0.70 thresholds illustrate trade-offs only; no threshold is
recommended. These are synthetic educational results, not airline estimates.

### Limitations and deployment status

The generator may encode bias; the sample is small and synthetic; external
validity, calibration, drift behaviour, causal interpretation, real airline
performance, and operational cost are not established. `departure_hour` is a
linear feature rather than a robust cyclic representation. There is no
production deployment, database, authentication, monitoring, or real-airline
validation. Docker and CI demonstrate reproducible local engineering only.

### Human oversight and decision boundary

The system provides training and decision-support evidence only. A real use
would require qualified operations review before any action, independent data
and model validation, documented threshold ownership, escalation for uncertain
or high-impact cases, auditability, and explicit authorization. No output may
be treated as an autonomous airline operational decision, safety certification,
or production authorization.

## Risk register

| Risk | Category | Likelihood | Impact | Existing control | Residual risk | Required gate/action |
|---|---|---:|---:|---|---|---|
| Synthetic generator bias | Data/model | Unknown | High | Synthetic status is explicit; limitations are documented | High | Real-data representativeness review before use |
| Generalization failure | Model | Unknown | High | Held-out split and leakage-safe feature contract | High | Independent temporal/route validation |
| Threshold misuse | Decision | Unknown | High | Thresholds are fixed educational examples; no recommendation | High | Governance owner must approve calibrated threshold |
| False positives / false negatives | Decision | Observed in benchmark | High | Confusion matrix and FP/FN extraction are tested | High | Human review and cost-sensitive validation |
| Overinterpretation or causal reading | Model | Plausible | Medium | Coefficients are labelled associations, not causes | Medium | Block causal or probability claims |
| API misuse | Security/operations | Unknown | Medium | Strict validation, deterministic adapter, no external side effects | Medium | Add access control and operational contract before exposure |
| Dependency/supply-chain risk | Security | Unknown | Medium | Version ranges and CI install path are visible | Medium | Pin/audit dependencies for any production build |
| Privacy risk if real data are introduced | Privacy | Conditional | High | Current data are synthetic and contain no PII | High if scope changes | Privacy review, minimization, access control, retention, and legal review |
| Production-readiness overclaim | Governance | Controlled | High | README and case study state local/training status | Low | Preserve wording during publication |
| Autonomous-decision overclaim | Governance/safety | Controlled | High | Explicit human boundary and prohibited-use statement | Low | Require human authorization for any real workflow |

Likelihood is qualitative or `Unknown` where repository evidence does not
support estimation; no quantitative probabilities are asserted.

## Evidence and traceability register

| Claim | Evidence | Verified result | Limitation |
|---|---|---|---|
| Classifier boundaries and semantics | `src/flight_delay_risk/classifier.py`; `tests/test_classifier.py` | Boundary, type, and error cases are covered | Rule thresholds are training rules, not operational policy |
| Data validation | `src/flight_delay_risk/operational_data.py`; `tests/test_operational_data.py` | Required fields, types, duplicates, and invalid values are rejected | CSV is synthetic and local |
| Analytics | `src/flight_delay_risk/analytics.py`; `tests/test_analytics.py` | SQLite-backed counts, thresholds, distributions, and deterministic outputs are tested | No OTP, network, passenger, or financial measures |
| Baseline ML | `src/flight_delay_risk/modeling.py`; `tests/test_modeling.py` | Dummy and logistic baselines, split, features, metrics, and explanations are exercised | Small synthetic benchmark; no production model |
| Leakage control | `src/flight_delay_risk/modeling.py`; `test_feature_contract_excludes_forbidden_fields` | Delay outcome, ID, and derived risk are excluded from features | Leakage review does not establish external validity |
| Evaluation and thresholds | `README.md`; modeling tests for confusion matrix and fixed thresholds | TN=27, FP=14, FN=3, TP=4 and educational threshold set are recorded | No recommended threshold or calibrated probability |
| Explainability | modeling tests and `explain_logistic_model` | Coefficients, directions, and odds ratios are exposed | Associations are not causal effects |
| FastAPI boundary | `src/flight_delay_risk/api.py`; `tests/test_api.py` | `/health`, `/risk`, strict validation, delegation, and no-side-effect behavior are tested | No auth, persistence, or production hardening |
| CI | `.github/workflows/test.yml` | GitHub Actions installs and runs pytest on Python 3.13 | Workflow execution is not a deployment pipeline |
| Docker | `Dockerfile`; README run instructions | Local image packaging and Uvicorn command are defined | No production scalability or security claim |
| Security review | This document, README, source/test inspection | No secrets, credentials, external operational API, PII, or autonomous action required | Future production controls are not implemented |

## Security and privacy boundary

### Implemented / evidenced now

- No secrets or credentials are required or embedded.
- No external operational API, production database, or persistent service is
  used by the training flow.
- The checked-in data is synthetic; no real passenger, crew, or proprietary
  operational PII is used.
- API validation rejects malformed, missing, extra, negative, and wrong-type
  inputs as tested.
- The API performs no autonomous external action.

These controls do not constitute GDPR compliance certification or a
cybersecurity certification.

### Future production controls — NOT IMPLEMENTED

If real airline data were introduced, the system would need a data protection
and threat-model review, minimization and retention rules, role-based access,
secret management, encryption, dependency and image scanning, authentication,
authorization, rate limiting, audit logging, incident response, model/data
lineage, monitoring, and formal validation. None of these future controls
should be read as present capabilities.

## W4 red-team disposition

Governance red team: **PASS** after explicitly separating rule engine from
predictive model, marking synthetic limits, removing production/safety/airline
claims, documenting threshold misuse, and defining human oversight.

Cybersecurity red team: **PASS** for the current local training scope. No
secret, credential, PII, unsafe operational example, exposed sensitive path,
or external-network assumption was found in the reviewed package. Residual
medium/low risks are listed above; no unresolved high finding remains for this
scope.

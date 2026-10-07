# Portfolio Evidence Index

## Five-minute inspection path

1. **Problem and scope** — read the [README landing page](../README.md) for
   the project purpose, architecture, accepted test evidence, and boundaries.
2. **Architecture and domain contract** — inspect
   [`src/flight_delay_risk/classifier.py`](../src/flight_delay_risk/classifier.py),
   [`operational_data.py`](../src/flight_delay_risk/operational_data.py), and
   the architecture section of the [case study](CASE_STUDY.md).
3. **Testing** — inspect [`tests/`](../tests/) and run `python -m pytest -v`;
   accepted W3 evidence is 79 passed, 0 failures.
4. **Analytics and model evidence** — inspect
   [`analytics.py`](../src/flight_delay_risk/analytics.py),
   [`modeling.py`](../src/flight_delay_risk/modeling.py), and the model/evaluation
   sections of the [case study](CASE_STUDY.md).
5. **API and reproducibility** — inspect [`api.py`](../src/flight_delay_risk/api.py),
   [`tests/test_api.py`](../tests/test_api.py), [`.github/workflows/test.yml`](../.github/workflows/test.yml),
   and [`Dockerfile`](../Dockerfile).
6. **Governance and security** — read the [governance package](GOVERNANCE.md)
   for the system/model card, risk register, evidence register, human boundary,
   privacy posture, and red-team dispositions.
7. **Limitations** — return to the [case study limitations](CASE_STUDY.md#limitations)
   and the README; synthetic data and non-production status are deliberate
   constraints, not hidden assumptions.

## Conservative portfolio claim

Designed and implemented an end-to-end aviation delay-risk training system
spanning validated synthetic operational data, analytics,
leakage-controlled baseline ML evaluation, a typed FastAPI service, automated
regression testing, CI/container reproducibility, and explicit governance,
security, human-oversight, and external-validity limitations.

## Not claimed

No production deployment, real-airline validation, safety certification,
production MLOps, autonomous decision-making, or realized financial benefit is
claimed.

# W1D1 Evidence

Date: 2026-08-20

Exercise: W1D1

Repository: flight-delay-risk-training

Starting HEAD: c3cc29d55a5c9d20e1282e5786639f4a9b271d6d

Starting test state: 8 passed

Learning objective: Complete one small, evidence-based software-engineering learning cycle by identifying and testing a meaningful boundary case in the flight delay risk classifier.

Boundary gap identified: Existing tests covered a 60-minute delay with weather risk and a 60-minute delay with crew issue as HIGH, but did not explicitly prove that a 60-minute delay with no weather risk and no crew issue remains MEDIUM.

Approved change: Add one boundary test for `classify_delay_risk(60, False, False)`.

Changed file: `tests/test_classifier.py`

Exact new test:

```python
def test_t_09_delay_at_60_without_risks_is_medium():
    assert classify_delay_risk(60, False, False) == "MEDIUM"
```

Final pytest result: 9 passed

Git diff summary:

- Added one test function to `tests/test_classifier.py`.
- Created this evidence record at `evidence/w1d1/README.md`.

Production code changed: No

Warnings observed: Pytest reported a cache-write warning because it could not write `.pytest_cache/v/cache/nodeids` in the Downloads repository path. This warning did not fail the test run.

Final technical result: PASS

Human Review status: APPROVED

Reviewer: Ihor

Decision: APPROVE

Technical result: PASS

Final W1D1 status: COMPLETE

#!/usr/bin/env python
"""Fail-closed validator for TB-002 human review completion evidence."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path


VALID_DECISIONS = {"APPROVE", "NEEDS_CHANGES", "REJECT"}


def non_empty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def valid_iso8601(value: object) -> bool:
    if not non_empty_string(value):
        return False
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        datetime.fromisoformat(normalized)
    except ValueError:
        return False
    return True


def main() -> int:
    path = Path(__file__).with_name("human_review.json")
    failures: list[str] = []

    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print("TB-002 HUMAN REVIEW VALIDATION: FAIL")
        print("human_review.json missing")
        return 2
    except json.JSONDecodeError as exc:
        print("TB-002 HUMAN REVIEW VALIDATION: FAIL")
        print(f"human_review.json invalid JSON: {exc}")
        return 2

    if record.get("tb_id") != "TB-002":
        failures.append("tb_id invalid")
    if record.get("record_type") != "HUMAN_REVIEW_COMPLETION_LAYER":
        failures.append("record_type invalid")
    if not non_empty_string(record.get("upstream_repository")):
        failures.append("upstream_repository missing")
    if not non_empty_string(record.get("upstream_evidence")):
        failures.append("upstream_evidence missing")
    if not non_empty_string(record.get("reviewer_identifier")):
        failures.append("reviewer_identifier missing")
    if not valid_iso8601(record.get("timestamp")):
        failures.append("timestamp missing or invalid ISO-8601")
    if record.get("decision") not in VALID_DECISIONS:
        failures.append("decision missing or invalid")
    if not non_empty_string(record.get("rationale")):
        failures.append("rationale missing")
    if record.get("completed") is not True:
        failures.append("completed != true")

    if failures:
        print("TB-002 HUMAN REVIEW VALIDATION: FAIL")
        for failure in failures:
            print(failure)
        return 1

    print("TB-002 HUMAN REVIEW VALIDATION: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

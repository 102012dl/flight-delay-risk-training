# Evidence Pack

## Project

flight-delay-risk-training

## Current Execution Date, Time, and Timezone

```text
2026-08-14 00:44:11 +02:00
```

## Working Directory

```text
C:\Users\home2\Downloads\ChatGPT Work Codex 1658 120826\flight-delay-risk-training
```

## Windows Sandbox Mode

```text
unelevated
```

## Python Version

```text
Python 3.13.15
```

## Pytest Version

```text
pytest 9.0.2
```

## Git Branch

```text
main
```

## Remote URL

```text
origin	https://github.com/102012dl/flight-delay-risk-training.git (fetch)
origin	https://github.com/102012dl/flight-delay-risk-training.git (push)
```

## Commit SHA

NOT AVAILABLE — no commit exists yet.

## Exact Pytest Command

```text
python -m pytest -v
```

## Complete Unedited Output From New Test Run Only

```text
============================= test session starts =============================
platform win32 -- Python 3.13.15, pytest-9.0.2, pluggy-1.6.0 -- C:\Users\home2\AppData\Local\Programs\Python\Python313\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\home2\Downloads\ChatGPT Work Codex 1658 120826\flight-delay-risk-training
configfile: pyproject.toml
testpaths: tests
plugins: anyio-4.9.0, langsmith-0.7.4, asyncio-1.3.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 8 items

tests/test_classifier.py::test_t_01_zero_delay_without_risks_is_low PASSED [ 12%]
tests/test_classifier.py::test_t_02_delay_under_30_with_risks_is_low PASSED [ 25%]
tests/test_classifier.py::test_t_03_delay_at_30_without_risks_is_medium PASSED [ 37%]
tests/test_classifier.py::test_t_04_delay_under_60_with_risks_is_medium PASSED [ 50%]
tests/test_classifier.py::test_t_05_delay_at_120_without_risks_is_high PASSED [ 62%]
tests/test_classifier.py::test_t_06_negative_delay_raises_value_error PASSED [ 75%]
tests/test_classifier.py::test_t_07_delay_at_60_with_weather_risk_is_high PASSED [ 87%]
tests/test_classifier.py::test_t_08_delay_at_60_with_crew_issue_is_high PASSED [100%]

============================== warnings summary ===============================
..\..\..\AppData\Local\Programs\Python\Python313\Lib\site-packages\_pytest\cacheprovider.py:475
  C:\Users\home2\AppData\Local\Programs\Python\Python313\Lib\site-packages\_pytest\cacheprovider.py:475: PytestCacheWarning: could not create cache path C:\Users\home2\Downloads\ChatGPT Work Codex 1658 120826\flight-delay-risk-training\.pytest_cache\v\cache\nodeids: [WinError 5] Access is denied: 'C:\\Users\\home2\\Downloads\\ChatGPT Work Codex 1658 120826\\flight-delay-risk-training\\pytest-cache-files-zg1ixy27'
    config.cache.set("cache/nodeids", sorted(self.cached_nodeids))

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 8 passed, 1 warning in 0.01s =========================
```

## Files Created

```text
.gitignore
README.md
pyproject.toml
src/flight_delay_risk/__init__.py
src/flight_delay_risk/classifier.py
tests/test_classifier.py
evidence/EVIDENCE_PACK.md
```

## Acceptance Mapping

| ID | Acceptance case | Result |
|---|---|---|
| T-01 | classify_delay_risk(0, False, False) == "LOW" | PASS |
| T-02 | classify_delay_risk(29, True, True) == "LOW" | PASS |
| T-03 | classify_delay_risk(30, False, False) == "MEDIUM" | PASS |
| T-04 | classify_delay_risk(59, True, True) == "MEDIUM" | PASS |
| T-05 | classify_delay_risk(120, False, False) == "HIGH" | PASS |
| T-06 | classify_delay_risk(-1, False, False) raises ValueError | PASS |
| T-07 | classify_delay_risk(60, True, False) == "HIGH" | PASS |
| T-08 | classify_delay_risk(60, False, True) == "HIGH" | PASS |

## Git Diff Check

Command:

```text
git diff --check
```

Output:

```text
```

Exit code: 0

## Git Status

Command:

```text
git status --short --branch
```

Complete output:

```text
## No commits yet on main
?? .gitignore
?? README.md
?? evidence/
?? pyproject.toml
?? src/
?? tests/
```

Exit code: 0

## Limitations

- No commit SHA exists yet.
- Files remain untracked.
- The pytest cache warning is an environment/sandbox limitation.
- The warning does not represent a functional test failure.
- The application is a controlled training artifact, not production software.

## Prohibited Actions Not Performed

- No installation.
- No git add.
- No commit.
- No push or pull.
- No fetch, clone, or init.
- No branch or pull request creation.
- No publication.

## Human Review Corrections

- Rebuilt `evidence/EVIDENCE_PACK.md` using the current pytest run only.
- Corrected the Acceptance Mapping Markdown table header.
- Added required governance sections.
- Preserved project implementation and tests without modification.

## Human Review Decision

PENDING — final external Human Review required.

## Recommended Next Action

Final Human Review before first commit and push.

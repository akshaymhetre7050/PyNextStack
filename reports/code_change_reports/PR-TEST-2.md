## Jira Issue
- **ID:** TEST-2
- **Summary:** [PyNextStack] Duplicate email/username check uses AND instead of OR, allowing duplicate accounts
- **Priority:** Medium
- **Assignee:** Unassigned
- **Link:** https://cybage-team-ykaip9am.atlassian.net/browse/TEST-2

## Defect Description
`user_exists()` in `app/routers/users.py` put both fields in one dict and wrapped it in a single-element `$or`. MongoDB therefore matched only users where **both** email AND username matched. A taken email paired with a new username (or the reverse) was reported as "available".

## Root Cause Analysis
`{"$or": [{"email": e, "username": u}]}` is a one-element `$or`, which is logically an AND. The correct form is `{"$or": [{"email": e}, {"username": u}]}`.

**Observed impact on `main` (verified against the running app):** the startup unique indexes on `users.email` and `users.username` stop a duplicate document from being written. A duplicate registration therefore fails with a generic **500** (`DuplicateKeyError` caught by `except Exception`), not 200 as the ticket's repro step says. `GET /api/v1/check_user_exists` returned the wrong answer (`false`) for a taken email + new username.

**After this fix:** `user_exists` and `/check_user_exists` return the correct answer. `POST /register/` and `POST /users/` now raise the intended 400, **but it is still converted into a 500** by the catch-all `except Exception`. That is TEST-3 and must be merged next for the message to reach users.

## Confluence Context Referenced
None found (space `SD` has no PyNextStack pages).

## Fix Summary
| File | Location | Before (Defective) | After (Fixed) | Reason |
|---|---|---|---|---|
| app/routers/users.py | user_exists:18-26 | `query = {}` … `{"$or": [query]}` | `conditions = []` … `{"$or": conditions}` | Each field becomes its own disjunct, so a match on either field is detected |

## Unit Tests Added
| Test File | Test | Coverage |
|---|---|---|
| tests/test_users.py | test_user_exists_existing_email_new_username_returns_true | Regression |
| tests/test_users.py | test_user_exists_new_email_existing_username_returns_true | Regression |
| tests/test_users.py | test_check_user_exists_endpoint_existing_email_new_username_returns_true | Regression (HTTP) |
| tests/test_users.py | test_user_exists_both_fields_match_returns_true / _new_email_and_username_returns_false / endpoint new user | Happy path |
| tests/test_users.py | email-only, username-only, no args, empty strings, endpoint no params → 400 | Edge cases |

Result: **11 passed**. The same suite against unfixed `main` gives **3 failed** (the regression tests).

## SAST / Quality Gate
- SonarQube: not run (`sonar.space` not configured)
- Bandit 1.9.4 on changed files: 0 issues in `app/routers/users.py`; 13 × Low B101 (`assert`) in the pytest file, which is expected
- Reviews: Adversarial → SHIP WITH FIXES (follow-ups only) · Code Review 2 → APPROVE · Code Quality 01 → PASS (max CC 4)

## Test Plan
- [x] Regression test: old buggy behaviour no longer occurs
- [x] Happy path: fix produces correct output for valid inputs
- [x] No regression in related existing functionality (callers' bool contract unchanged)
- [x] Unit tests pass locally (`pip install -r requirements-dev.txt && pytest tests/test_users.py`)

## Fix Checklist
- [x] Fix is minimal — only the defect is changed
- [x] No unrelated refactoring or cleanup
- [x] Regression + happy path + edge case tests added
- [x] SAST clean (Bandit)
- [x] Jira issue updated

## Follow-ups
- TEST-3: re-raise `HTTPException` so duplicates return 400, not 500
- New bug suggested: email uniqueness is case-sensitive

Reports: `reports/code_change_reports/`, `reports/adversarial/`, `reports/code-review-2/`, `reports/code-quality/`, `reports/unit_test_reports/TEST-2/`

🤖 Generated with [Claude Code](https://claude.com/claude-code)

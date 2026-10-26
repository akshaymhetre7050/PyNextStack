# Adversarial — Blockers & Commit Readiness (2026-10-26)

**Branch:** `feature/TEST-2-duplicate-user-check` | **Jira:** TEST-2

## Blockers (P0)
None.

## Must-address before the TEST-2 behaviour is user-visible (P1)

| # | Finding | Location | In this PR? | Owner / ticket |
|---|---|---|---|---|
| 1 | HTTPException(400) swallowed into 500 in the create handlers | `register.py:61`, `users.py:115` | No (pre-existing) | **TEST-3** |
| 2 | Email uniqueness is case-sensitive | `users.py:18-26`, `initial_settings.create_indexes` | No (pre-existing) | Recommend a new Jira bug |

## Readiness checklist

| Check | Status |
|---|---|
| Fix limited to the defect | ✅ |
| Regression tests fail on old code / pass on new | ✅ 3 fail → 11/11 pass |
| SAST on changed files | ✅ Bandit: 0 issues in `users.py`; 13 × Low B101 (`assert`) in tests, which is expected for pytest |
| Callers verified (`register.create_user`, `users.create_user`, `users.check_user_exists`) | ✅ Contract unchanged (returns bool) |
| Secrets / PII in diff | ✅ None |

## Decision
**READY TO MERGE** as a scoped fix. Merge TEST-3 next so duplicate registration returns 400 instead of 500.

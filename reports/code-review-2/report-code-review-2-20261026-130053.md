# Code Review Report

**Skill:** code-review 2 (Secure-Engineering-Code-Review/security/code-review 2.md)
**Branch:** `feature/TEST-2-duplicate-user-check` vs `main` (merge-base `7546865`)
**Generated:** 2026-10-26 13:00:53

> **Context adaptation.** This skill is written for a React/MUI/TypeScript component library. This diff only touches the **Python/FastAPI backend**, so the frontend-specific conventions (forwardRef, displayName, Storybook, RTL, lodash, Prettier/ESLint) do not apply and are marked N/A. The four review domains (architecture, documentation, resilience, testing) and the severity scale were applied to the Python code. The diff is 3 source files and about 120 code lines, so the four domain passes ran in sequence in one reviewer instead of as parallel subagents.

## Summary
The change correctly fixes the `$or` defect in `user_exists` and adds 11 targeted tests that fail on the old code and pass on the new. There are no Critical or High issues. Two Medium findings are pre-existing behaviours in the surrounding code that limit the fix's user-visible effect, and should be tracked separately. **Recommendation: APPROVE.**

## Diff Statistics
- Files changed: 5 (3 source/config, 2 generated reports)
- Insertions: 1240 (≈118 code, rest generated HTML) | Deletions: 5
- Review scope: `user_exists` `$or` fix, new pytest suite, dev requirements

## Formatting & Lint
Prettier/ESLint: N/A (no JS/TS files changed). Python: Bandit 1.9.4 on changed files found 0 issues in `app/routers/users.py` and 13 × Low B101 (`assert_used`) in `tests/test_users.py`, which is expected for pytest. No auto-fixes were needed.

## Critical Issues
None.

## Architecture Issues

| Severity | Location | Problem | Fix |
|---|---|---|---|
| Medium | app/routers/register.py:61 | The create handler's `except Exception` swallows the 400 that `user_exists` now triggers, so a duplicate registration still returns 500 (verified live). | Add `except HTTPException: raise` before the catch-all. Tracked as **TEST-3**. See also: app/routers/users.py:115 |
| Medium | app/routers/users.py:18 | Email comparison is case-sensitive in both the `$or` query and the unique index, so `Alice@x.com` and `alice@x.com` are treated as different users. | Lower-case the email on write and lookup, or rebuild the index with collation `{locale:'en', strength:2}`. Raise as a new bug. |
| Low | app/routers/users.py:18 | `email: str = None` is implicitly Optional. | `email: str \| None = None`. |

### Breaking Change Assessment

| File | Change Type | Consumer Impact | Migration Path |
|---|---|---|---|
| app/routers/users.py | Behaviour fix | `GET /api/v1/check_user_exists` now returns `true` when *either* field is taken. The Next.js app does not call it. | None needed |

## Lodash Usage
N/A (Python change).

## Resilience & Performance Issues

| Severity | Location | Problem | Fix |
|---|---|---|---|
| Low | app/routers/register.py:28-50 | Check-then-insert race. The unique index protects the data, but the losing request gets a 500 from `DuplicateKeyError`. | Catch `pymongo.errors.DuplicateKeyError` and return 400. |

Performance: the `$or` is on two fields that each have a unique index, so MongoDB answers it with an index union. No collection scan. ✅

### Accessibility Audit
N/A (no UI change).

## Documentation Gaps

| Severity | Location | Problem | Fix |
|---|---|---|---|
| Low | app/routers/users.py:18 | `user_exists` has no docstring stating its OR semantics, which is the exact contract this bug violated. | Add a one-line docstring: "True if any user has the given email OR username." |

### Missing Storybook Coverage
N/A.

## Testing & Type Safety

| Severity | Location | Problem | Fix |
|---|---|---|---|
| Low | requirements-dev.txt:2-5 | Test dependencies are unpinned, so CI is not reproducible. | Pin versions: `pytest~=9.1`, `pytest-asyncio~=1.4`, `pytest-html~=4.2`, `mongomock-motor~=0.0.36`. |

### Coverage Gaps

| Location | Code Path | Test Needed |
|---|---|---|
| app/routers/register.py:28 | `POST /register/` duplicate → 400 | `test_register_duplicate_email_returns_400` (add with TEST-3) |
| app/routers/users.py:93 | `POST /users/` duplicate → 400 | `test_create_user_duplicate_username_returns_400` (add with TEST-3) |

## Positive Patterns
1. **Proven regression.** The tests were executed against unfixed `main` (3 fail) and the fix (11 pass). Reviewers can trust the tests detect this bug.
2. **Realistic test double.** mongomock-motor evaluates real `$or` semantics, so the tests check query behaviour, not a mocked return value.
3. **Minimal diff.** 5 lines changed, with the function signature and return contract preserved for all three callers.

## Verdict

**Decision:** APPROVE

| Severity | Count |
|---|---|
| Critical | 0 |
| High | 0 |
| Medium | 2 |
| Low | 4 |
| **Total** | 6 |

**Blocking Issues:** None. The Medium items are pre-existing and are tracked in TEST-3 or recommended as a new ticket.

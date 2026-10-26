# Adversarial — First Commit Detailed Report (2026-10-26)

**Commit:** `2f6ccf7` — fix(TEST-2): detect existing email OR username in user_exists
**Branch:** `feature/TEST-2-duplicate-user-check` (base `main` @ `7546865`)

## Files in commit

| File | Change | Lines | Adversarial verdict |
|---|---|---|---|
| `app/routers/users.py` | Fix | +5 / −5 | Correct. No new risk introduced. |
| `tests/test_users.py` | New | +103 | Good. Covers regression, happy path and edge cases. Missing handler-level duplicate tests (blocked by TEST-3). |
| `requirements-dev.txt` | New | +5 | OK. Test deps are unpinned (pytest, pytest-asyncio, pytest-html, mongomock-motor); pin them for reproducible CI (P2). |
| `reports/unit_test_reports/TEST-2/*` | New | report artefacts | Generated output; not reviewed for code quality. |

## Line-by-line on the fix

| Line | Before | After | Assessment |
|---|---|---|---|
| 19 | `query = {}` | `conditions = []` | Correct type for an `$or` operand. The name describes the content. |
| 21 | `query["email"] = email` | `conditions.append({"email": email})` | Each field is now its own disjunct. |
| 23 | `query["username"] = username` | `conditions.append({"username": username})` | Same. |
| 24–25 | `{"$or": [query]}` | `{"$or": conditions}` | Root-cause fix. A single-element `$or` was equivalent to AND. |

## Behaviour matrix (seed user: alice / alice@example.com)

| email arg | username arg | Before | After | Correct? |
|---|---|---|---|---|
| alice@example.com | bob | False ❌ | True | ✅ |
| bob@example.com | alice | False ❌ | True | ✅ |
| alice@example.com | alice | True | True | ✅ |
| bob@example.com | bob | False | False | ✅ |
| alice@example.com | — | True | True | ✅ |
| — | alice | True | True | ✅ |
| — / "" | — / "" | False | False | ✅ |
| Alice@Example.com | bob | False | False | ⚠️ case-sensitive (P1 follow-up) |

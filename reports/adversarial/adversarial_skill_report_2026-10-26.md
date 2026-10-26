# Adversarial Review — TEST-2 fix (`feature/TEST-2-duplicate-user-check`)

**Skill:** adversarial-agent (Secure-Engineering-Code-Review/adversarial/SKILL.md)
**Scope:** diff `main..feature/TEST-2-duplicate-user-check`: `app/routers/users.py` (`user_exists`), `tests/test_users.py`, `requirements-dev.txt`
**Date:** 2026-10-26

## 🔍 Code Review — `app/routers/users.py::user_exists` + `tests/test_users.py`

**Assumptions**
> - Python 3.14 / FastAPI 0.110 / Motor (async MongoDB). Reviewed the diff only, plus surrounding context where it creates risk.
> - `app/components/initial_settings.py::create_indexes` runs at startup and creates unique indexes on `users.email` and `users.username`. This was verified on the local DB (`email_1`, `username_1`, both `unique: True`).

### Summary Scorecard

| Lens | Status | Finding Count |
|------|--------|---------------|
| Brevity & DRY | 🟢 Clean | 0 |
| Readability & Naming | 🟡 Minor issues | 1 |
| Performance & Complexity | 🟢 Clean | 0 |
| Security & Robustness | 🟡 Minor issues | 3 |
| Test Coverage | 🟡 Minor issues | 1 |

**Overall Verdict:** `SHIP WITH FIXES`. The diff is correct and proven by tests. The "fixes" are follow-ups in surrounding code, not changes to this diff.

> Biggest risk if merged as-is: users still see a generic **500** instead of the 400 "already in use" message on duplicate registration, because of TEST-3 (HTTPException swallowed). This fix only becomes user-visible once TEST-3 lands.

### Findings

```
[P1 IMPORTANT]  Lens: Security & Robustness
─────────────────────────────────────────────────────────────
WHAT:   The fixed check is still not user-visible on POST /register/ and POST /users/
WHY:    user_exists now raises HTTPException(400) correctly, but the surrounding `except Exception`
        in both create handlers turns it into a 500. Verified live: on unfixed main a duplicate-email
        registration returns 500 (from DuplicateKeyError). With this fix it still returns 500 (from the
        swallowed 400).
WHERE:  app/routers/register.py:61, app/routers/users.py:115 (pre-existing; tracked as TEST-3)
HOW:    Merge TEST-3 next: add `except HTTPException: raise` before `except Exception`, as delete_user does.
```

```
[P1 IMPORTANT]  Lens: Security & Robustness
─────────────────────────────────────────────────────────────
WHAT:   Uniqueness is case-sensitive ("Alice@Example.com" is not seen as "alice@example.com")
WHY:    Pydantic's EmailStr keeps the local-part case, and both the $or query and the unique index compare
        exactly. A user can register the same mailbox twice with different casing. This bypasses the
        intent of TEST-2.
WHERE:  app/routers/users.py:18-26 (user_exists); initial_settings.create_indexes
HOW:    Normalise on write and on lookup: `email = email.strip().lower()`. Alternatively, build the indexes
        with a case-insensitive collation:
        create_index("email", unique=True, collation={"locale": "en", "strength": 2})
        Existing data must be checked for case-duplicates before rebuilding the index.
```

```
[P2 SUGGESTION]  Lens: Security & Robustness
─────────────────────────────────────────────────────────────
WHAT:   Check-then-insert is not atomic (TOCTOU)
WHY:    Two concurrent registrations can both pass user_exists. The unique index still prevents a duplicate
        document (data is safe), but the loser gets a 500 from DuplicateKeyError instead of a 400.
WHERE:  app/routers/register.py:28-50, app/routers/users.py:93-108
HOW:    Catch pymongo.errors.DuplicateKeyError around insert_one and map it to the same 400.
```

```
[P2 SUGGESTION]  Lens: Security & Robustness
─────────────────────────────────────────────────────────────
WHAT:   GET /check_user_exists now answers correctly, which makes it a precise enumeration oracle
WHY:    The endpoint sits behind the users router's JWT dependency, so only logged-in users can probe it.
        Still, any authenticated "user" role can now test arbitrary emails. Related to TEST-5.
WHERE:  app/routers/users.py:74-86
HOW:    Add rate-limiting (Redis is already in place) or restrict it with check_permissions.
```

```
[P2 SUGGESTION]  Lens: Readability & Naming / Test Coverage
─────────────────────────────────────────────────────────────
WHAT:   No endpoint-level test for POST /register/ or POST /users/ duplicate rejection;
        `email: str = None` hints are implicitly Optional
WHY:    The tests prove user_exists and /check_user_exists, but not the two handlers named in TEST-2's
        Expected section. These tests cannot pass until TEST-3 is fixed.
WHERE:  tests/test_users.py; app/routers/users.py:18
HOW:    Add `test_register_duplicate_email_returns_400` alongside the TEST-3 fix.
        Use `email: str | None = None`.
```

### Minor notes
- The test fixture monkeypatches the module-global `users.user_collection`. This works because `register.py` imports the `user_exists` function, which resolves the global at call time. Dependency injection would be cleaner, but it is out of scope.
- `"alice@example.com"` is repeated in tests. `EXISTING_USER["email"]` could be reused (P2, cosmetic).

### Refactored Snippet
Not needed. The changed block is 8 lines with no clustered findings.

### What's Working Well
- **The fix is minimal and correct.** The `$or` array now holds one condition per field. Single-field lookups and the "no criteria → False" behaviour are unchanged, so all three callers keep their contract.
- **The regression is proven, not assumed.** The same 11 tests were run against unfixed `main`. Exactly the 3 regression tests failed, and all 11 pass after the fix.
- **The tests exercise the real code path.** They call the real `user_exists` and the real FastAPI route via `httpx.ASGITransport`. Only the Mongo collection is replaced, with an in-memory mongomock-motor instance, so `$or` semantics are actually evaluated.
- **Truthy guards (`if email:`) treat empty strings as absent.** This is covered by `test_user_exists_empty_strings_returns_false`, so `""` cannot match every user missing an email field.

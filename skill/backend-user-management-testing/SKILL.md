---
name: backend-user-management-testing
description: Test and validate AutoGeo backend user management and auth flows (user CRUD, role-based access, login/refresh/logout). Use when asked to design or run tests for /api/users or /api/auth endpoints.
---

# Backend User Management Testing

## Quick start

- Run focused tests: `python -m pytest tests/test_api/test_users.py tests/test_api/test_auth.py -v`

## Standard workflow

1. Verify dependencies:
   - Python 3.10+
   - `pip install -r backend/requirements.txt`
2. Run in-memory API tests (preferred for user management):
   - `python -m pytest tests/test_api/test_users.py -v`
3. If adding cases, follow the in-memory TestClient pattern:
   - Create an in-memory SQLite engine
   - Override `get_db`
   - Seed admin/user records with hashed passwords
4. Validate the checklist in `references/user-management-test-cases.md`.
5. Record evidence:
   - Test command
   - Failures with status codes and response bodies
   - Any environment assumptions

## Files to update

- Tests: `tests/test_api/test_users.py`
- Auth/permissions tests: `tests/test_api/test_auth.py`
- Reference checklist: `references/user-management-test-cases.md`

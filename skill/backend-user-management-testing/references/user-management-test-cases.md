# User management test checklist

## Preconditions

- Use in-memory SQLite unless explicitly testing the real DB.
- Create an admin user for all admin-only routes.
- Use `/api/auth/login` to get a bearer token.

## Core CRUD cases

1. Create user (admin):
   - POST `/api/users`
   - Expect 200, response includes `id`, `username`, `role`, `status`.
   - Duplicate username should return 400.
2. List users (admin):
   - GET `/api/users`
   - Expect 200 and list includes admin + created users.
3. Get user by id (admin):
   - GET `/api/users/{id}`
   - Expect 200 for existing, 404 for missing.
4. Update user (admin):
   - PUT `/api/users/{id}`
   - Update email, role, status, password.
   - Expect 200 and updated fields.
5. Disable user (admin):
   - DELETE `/api/users/{id}`
   - Expect 200 and message indicates disabled.

## Auth and status cases

1. Login success:
   - POST `/api/auth/login` with active user
   - Expect 200 and access token.
2. Login blocked for disabled user:
   - After disabling, login should return 401.
3. Password update:
   - After updating password, login with new password should succeed.

## Authorization cases

1. Non-admin access:
   - GET or POST `/api/users` with non-admin token
   - Expect 403.

## Evidence to capture

- Test commands executed
- Status codes + response snippets for failures
- Any deviations from in-memory setup

# Security Notes

## Purpose
This document captures the current security posture of SkillBridge, the decisions already implemented, and the gaps that should be addressed before a serious public launch.

## Current Controls

### Authentication
- Supabase Auth is used for email/password signup and login.
- Local Flask sessions do not authenticate users by password directly anymore.
- Supabase access and refresh tokens are restored and revalidated on each request.
- Local application profiles are linked to Supabase identities through `users.auth_user_id`.

### Session Security
- `SESSION_COOKIE_HTTPONLY` is enabled.
- `REMEMBER_COOKIE_HTTPONLY` is enabled.
- In production, secure cookies are enabled through:
  - `SESSION_COOKIE_SECURE=True`
  - `REMEMBER_COOKIE_SECURE=True`
- SameSite is set to `Lax` for session and remember cookies.

### Transport and Proxy Handling
- The Flask app uses `ProxyFix` so forwarded HTTPS headers from Render are interpreted correctly.
- Production deployment assumes TLS is terminated by Render.

### Authorization
- Session and review operations check that the current user is part of the relevant record.
- Skill deletion routes scope deletes to the logged-in user's own rows.
- Exchange status transitions are limited by requester/provider role and current status.

### Secrets
- Production startup requires `SECRET_KEY`.
- Supabase credentials are expected through environment variables, not hardcoded values.

## Current Risks

### Missing CSRF Protection
Forms currently do not use CSRF tokens. This is the most obvious security gap in the current app.

### Broad Supabase Key Usage
The application currently uses one configured Supabase key for both auth interactions and data operations. This works operationally, but it is not the final least-privilege model we want.

### No Row Level Security Policy Documentation
The repo does not yet define or document Supabase RLS policies for the tables the app reads and writes.

### Limited Input Validation
Basic validation exists, but stricter length, format, and business-rule validation should be added consistently across all mutating routes.

### Sparse Auditability
There is no dedicated audit log, no structured security event logging, and no alerting on suspicious auth behavior.

## Required Pre-Launch Improvements
1. Add CSRF protection to all forms.
2. Define and apply Supabase RLS policies for all application tables.
3. Separate privileged backend access from public client-style configuration more deliberately.
4. Add stricter validation and error handling around all writes.
5. Add rate limiting for auth endpoints.
6. Add structured logging for auth failures, profile linking failures, and abnormal session behavior.

## Supabase Checklist
1. Enable only the auth providers you intend to support.
2. Set `Site URL` to the Render production domain.
3. Add local and production redirect URLs explicitly.
4. Review email confirmation requirements.
5. Review password policy and brute-force protections in the Supabase dashboard.

## Render Checklist
1. Set `SECRET_KEY`, `SUPABASE_URL`, and `SUPABASE_KEY` as environment variables.
2. Keep `FLASK_ENV=production`.
3. Keep `FLASK_DEBUG=0`.
4. Do not commit live `.env` files or exported Supabase secrets.

## Team Guidance
- Never paste production secrets into source files.
- Prefer SQL migration scripts for schema changes that affect auth or authorization.
- Treat credit settlement logic as financial logic and review carefully before changing it.
- Any route that mutates data should be reviewed for both authentication and ownership checks.

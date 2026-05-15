# SkillBridge Architecture

## Overview
SkillBridge is a Flask web application for peer-to-peer skill exchange. Students create profiles, publish skills they can teach, list skills they want to learn, discover ranked matches, request exchange sessions, and settle time-credit transactions after both sides confirm completion.

The current architecture is a server-rendered Flask app backed by Supabase for both authentication and PostgreSQL data storage, with Render as the target hosting platform.

## Runtime Architecture

### Application Layer
- Flask application factory in [app/__init__.py](/D:/APPS/Skill-bridge/app/__init__.py)
- Jinja templates for server-rendered UI
- Flask-Login for local session state
- Supabase session restoration on each request using stored access and refresh tokens

### Data and Auth Layer
- Supabase Auth for email/password signup, login, and session verification
- Supabase Postgres for application tables
- Direct Supabase table queries from Python, without an ORM

### Hosting Layer
- Render web service for production deployment
- Gunicorn process manager for serving Flask
- Health endpoint at `/healthz` for Render health checks

## Core Components

### Auth Module
- File: [app/auth.py](/D:/APPS/Skill-bridge/app/auth.py)
- Handles Supabase signup and login
- Links Supabase auth users to local user profiles through `users.auth_user_id`
- Stores Supabase access and refresh tokens in the Flask session
- Manages profile editing and initial welcome credits

### Skills Module
- File: [app/skills.py](/D:/APPS/Skill-bridge/app/skills.py)
- Renders dashboard metrics
- Supports adding and deleting offered and wanted skills
- Supports marketplace-style browsing of active skill offers
- Produces ranked skill matches from domain helpers

### Exchange Module
- File: [app/exchange.py](/D:/APPS/Skill-bridge/app/exchange.py)
- Creates exchange requests
- Enforces basic request validation
- Manages request lifecycle states: `pending`, `accepted`, `rejected`, `cancelled`, `completed`
- Settles time-credit transactions when both sides confirm completion

### Feedback Module
- File: [app/feedback.py](/D:/APPS/Skill-bridge/app/feedback.py)
- Allows reviews only for completed sessions
- Prevents out-of-session review submission

### Domain Helpers
- File: [app/domain.py](/D:/APPS/Skill-bridge/app/domain.py)
- Centralizes shared query helpers and business logic
- Enriches skill records with names and descriptions
- Computes dashboard metrics, balances, reputations, and match recommendations
- Provides credit ledger helpers

## Data Model

### Primary Tables
- `users`
- `skills`
- `user_skill_offers`
- `user_skill_wants`
- `exchange_sessions`
- `credit_transactions`
- `reviews`

### Important Relationships
- `users.auth_user_id` links a local profile to a Supabase Auth identity
- `user_skill_offers.user_id` and `user_skill_wants.user_id` reference `users.id`
- `exchange_sessions.requester_id` and `exchange_sessions.provider_id` reference `users.id`
- `credit_transactions.session_id` optionally references `exchange_sessions.id`
- `reviews.session_id` references `exchange_sessions.id`

## Request Flow

### Signup
1. User submits registration form.
2. Flask calls Supabase Auth `sign_up`.
3. App creates or links the matching profile in `users`.
4. App inserts a `credit_transactions` welcome record with `+100`.
5. If Supabase returns an active session immediately, Flask logs the user in locally.

### Login
1. User submits email and password.
2. Flask calls Supabase Auth `sign_in_with_password`.
3. App resolves the linked profile by `auth_user_id`.
4. Access and refresh tokens are saved in the Flask session.
5. Flask-Login signs in the local app user.

### Authenticated Request
1. Flask reads `sb_access_token` and `sb_refresh_token` from the session.
2. App rehydrates the Supabase session using `set_session`.
3. App verifies the current auth user from Supabase.
4. App maps that auth user back to a local profile and refreshes Flask-Login state.

## Deployment Model

### Render
- Start command: `gunicorn run:app`
- Health path: `/healthz`
- Required environment variables:
  - `SECRET_KEY`
  - `SUPABASE_URL`
  - `SUPABASE_KEY`
  - `FLASK_ENV=production`
  - `FLASK_DEBUG=0`

### Supabase
- Email auth provider enabled
- Redirect URLs configured for local development and Render production domain
- SQL migration applied to support `users.auth_user_id`

## Current Architectural Decisions
- No ORM layer
- Server-rendered Flask app rather than SPA frontend
- Supabase is the system of record for auth and relational data
- Credit balance is derived from the latest credit transaction, not stored directly on the user row

## Current Strengths
- Clear modular route structure
- Real external auth provider integration
- Server-side rendered flows that are simple to deploy on Render
- Marketplace-style matching and session lifecycle already implemented

## Known Gaps
- No CSRF protection yet
- No Supabase Row Level Security policy documentation in repo yet
- No formal migrations framework beyond SQL scripts
- No end-to-end browser test coverage
- No background jobs or async notifications

## Near-Term Next Steps
1. Add CSRF protection and tighter form validation.
2. Introduce Supabase RLS policies and document them.
3. Add route-level tests for auth, skill management, and session transitions.
4. Add scheduling/location details to the session workflow.
5. Add production observability and deployment runbooks.

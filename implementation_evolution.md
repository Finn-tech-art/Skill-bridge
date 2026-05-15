# SkillBridge Implementation Evolution Report

## Purpose
This document comes after the original proposal, requirements specification, feasibility study, and system design documents. Its purpose is to explain how the implemented SkillBridge system evolved from the initial plan, what changed during development, why those changes were made, and how the current architecture behaves in practice.

It should be read as the bridge between the early project documents and the live codebase.

## Source Documents Considered
- `BIT 2221 GROUP 5 Proposal.docx`
- `Requirements Specification.docx`
- `Feasibility Study.docx`
- `System Design.docx`
- `SkillBridge_System_Design.docx`

## What The Initial Documents Proposed

Across the original project documents, SkillBridge was defined as:
- a peer-to-peer skill exchange platform for university students
- a web-based system built with Flask
- a three-tier architecture with presentation, application, and data layers
- a MySQL-backed relational system
- a session-based authentication system
- a product centered on:
  - registration and login
  - profile management
  - skill listing and discovery
  - skill matching
  - session scheduling and confirmation
  - time-credit and direct-swap exchange models
  - reviews and reputation

The original documents also emphasized:
- modular design
- fairness and transparency in credit handling
- secure handling of user data
- maintainability
- suitability for the university environment

## Why The Implementation Evolved

As development moved from planning to a working product, several practical realities influenced the system:

1. The backend needed a simpler operational model.
The original plan assumed Flask + MySQL with more traditional app-managed authentication and database handling. During implementation, the project moved toward Supabase so that authentication, hosted PostgreSQL, and cloud persistence could be handled by a single external platform.

2. The app needed a faster path to deployment.
The project moved from a largely local-development mindset to a real cloud deployment path using Render. That required changes to configuration, startup strategy, session handling, and documentation.

3. The domain model was richer than the first UI.
The schema already supported exchange states, credit history, wanted-skill priorities, and direct-swap vs time-credit behavior, but the early templates did not expose that depth. Later phases brought the interface closer to the intended product logic.

4. Trust and legitimacy became product concerns, not just technical concerns.
Because the deployed app had authentication, credit logic, and public sign-in pages, the team had to address browser trust signals, clearer public-facing pages, and visible policies.

## Major Changes From The Initial Plan

### 1. Database and Platform Change

#### Original Plan
- MySQL as the primary database
- more conventional app-managed data access

#### Current Implementation
- Supabase Postgres is now the primary data store
- Supabase Auth handles email/password account identity
- the Flask app uses direct Supabase table queries instead of an ORM

#### Why This Changed
- reduced infrastructure complexity
- easier hosted backend setup
- simpler path to production deployment
- tighter integration between identity and relational data

### 2. Authentication Strategy Change

#### Original Plan
- session-based authentication managed mainly inside the Flask application
- password hashing and verification handled locally

#### Current Implementation
- Supabase Auth now handles signup and login
- the local `users` table is linked to Supabase identities through `users.auth_user_id`
- Flask-Login is still used, but only as the local session wrapper for an already verified Supabase identity
- Supabase access and refresh tokens are stored in the Flask session and restored on each request

#### Why This Changed
- stronger external auth model
- easier email confirmation flow
- better alignment with cloud deployment
- reduced need for the Flask app to be the system of record for credentials

### 3. Credit System Realization

#### Original Plan
- the credit ledger was conceptualized as a fairness mechanism where teaching earns credits and learning spends them

#### Current Implementation
- a `credit_transactions` table is the ledger source of truth
- user balance is derived from the latest ledger row rather than stored directly on the profile
- new accounts receive `100` welcome credits
- time-credit exchanges settle only after both participants confirm completion

#### Why This Changed
- keeps the system auditable
- makes balance history explainable
- reduces the risk of silent balance drift

### 4. Matching Logic Enhancement

#### Original Plan
- matching based on offered skills vs wanted skills
- references to ranking factors such as compatibility, ratings, and exchange mode

#### Current Implementation
- matching is weighted using:
  - wanted-skill priority
  - provider proficiency level
  - verification flags
  - reputation
  - reciprocal skill overlap
- the engine now distinguishes between direct-swap potential and time-credit recommendations

#### Why This Changed
- simple skill overlap was not enough for useful recommendations
- the product needed to prefer more practical exchanges over merely possible ones

### 5. Session Lifecycle Realization

#### Original Plan
- users should be able to request, schedule, confirm, cancel, and complete exchange sessions

#### Current Implementation
- implemented states include:
  - `pending`
  - `accepted`
  - `rejected`
  - `cancelled`
  - `completed`
- role-based transitions are enforced in the app
- both participants must confirm completion before settlement
- review submission is restricted to completed sessions

#### What Is Still Partial
- richer scheduling details like real calendar coordination, location planning, and availability overlap are still limited

### 6. UI/UX Direction Change

#### Original Plan
- HTML, CSS, Bootstrap, and JavaScript
- straightforward university project UI

#### Current Implementation
- still server-rendered with Flask and Jinja
- custom CSS replaced the earlier wireframe-style interface
- the product was redesigned toward a marketplace-style experience inspired by modern service platforms
- public trust pages were added:
  - About
  - Privacy
  - Terms
  - Contact

#### Why This Changed
- the original UI did not communicate enough product trust
- deployed authentication screens needed stronger brand and legitimacy signals
- the product needed to feel like a real exchange marketplace, not a classroom demo

### 7. Deployment Architecture Change

#### Original Plan
- local or controlled network deployment during development
- optional free-tier cloud hosting

#### Current Implementation
- the app is prepared for deployment on Render
- Gunicorn is used as the production app server
- a health check endpoint exists at `/healthz`
- repo-level deployment configuration now exists through:
  - `Procfile`
  - `render.yaml`
  - production-ready environment variable documentation

#### Why This Changed
- the project progressed beyond local-only testing
- the system needed a stable hosted URL for Supabase Auth and public access

## How The New Architecture Behaves

## Runtime Overview
The current system is best understood as a Flask application sitting in front of Supabase.

- Flask handles routing, templates, business logic, and local session state
- Supabase Auth handles identity verification
- Supabase Postgres stores the application data
- Render hosts the running web service

## Request Lifecycle

### Signup Flow
1. A user submits the registration form.
2. Flask sends the registration request to Supabase Auth.
3. Supabase creates the auth identity.
4. Flask creates or links the corresponding application profile in `users`.
5. Flask inserts the welcome credit ledger entry.
6. If Supabase returns an active session immediately, Flask signs in the local app user.

### Login Flow
1. A user submits email and password.
2. Flask calls Supabase `sign_in_with_password`.
3. Supabase validates the credentials.
4. Flask resolves the local profile using `auth_user_id`.
5. Flask stores access and refresh tokens in the session.
6. Flask-Login marks the user as authenticated in the app.

### Authenticated Request Flow
1. On each request, Flask reads the stored Supabase session tokens.
2. The app restores the Supabase session with `set_session`.
3. The app verifies the current Supabase user.
4. The app reloads the matching local profile.
5. The request continues as an authenticated app user.

## Architectural Layers In Practice

### Presentation Layer
- Jinja templates under [app/templates](/D:/APPS/Skill-bridge/app/templates)
- custom CSS in [app/static/css/main.css](/D:/APPS/Skill-bridge/app/static/css/main.css)
- server-rendered pages rather than a separate SPA frontend

### Application Layer
- app factory and session restoration in [app/__init__.py](/D:/APPS/Skill-bridge/app/__init__.py)
- auth logic in [app/auth.py](/D:/APPS/Skill-bridge/app/auth.py)
- skill routes in [app/skills.py](/D:/APPS/Skill-bridge/app/skills.py)
- exchange lifecycle in [app/exchange.py](/D:/APPS/Skill-bridge/app/exchange.py)
- review flow in [app/feedback.py](/D:/APPS/Skill-bridge/app/feedback.py)
- shared business logic in [app/domain.py](/D:/APPS/Skill-bridge/app/domain.py)

### Data Layer
- relational schema in [db/schema.sql](/D:/APPS/Skill-bridge/db/schema.sql)
- Supabase tables used directly from Python
- no ORM abstraction layer

## How The Main Modules Behave Now

### Authentication Module
- creates accounts through Supabase Auth
- links auth identities to app profiles
- supports profile editing after login
- supports welcome credit initialization

### Profile Management Module
- implemented as part of the auth/profile flow
- supports updating:
  - full name
  - department
  - year of study
  - bio

### Skill Management Module
- users can add offered skills
- users can add wanted skills
- skills can be browsed across the platform
- user-owned skill records can be removed
- new skills can be created dynamically in the catalogue if needed

### Matching Engine Module
- ranks providers for a learner’s wanted skills
- uses priority, proficiency, verification, reputation, and reciprocity
- recommends direct swap where reciprocal value exists

### Exchange Management Module
- creates exchange requests
- prevents invalid or duplicate active requests
- supports provider acceptance or rejection
- supports cancellation
- supports double-confirmation completion

### Credit Ledger Module
- records every welcome, earned, spent, or adjustment event
- derives balances from the ledger
- records session-linked settlements for time-credit exchanges

### Feedback and Reputation Module
- allows reviews only for completed sessions
- calculates reputation from received reviews

## Where The Implementation Still Differs From The Full Original Vision

The current system is substantially functional, but it does not yet fully implement everything implied in the original documents.

### Not Fully Realized Yet
- full scheduling workflow with robust start/end planning
- availability matching
- avatar upload and richer profile media
- admin or moderation role
- formal reporting dashboards
- comprehensive testing beyond the current baseline
- CSRF protection
- documented Supabase Row Level Security policies

## Why The Current Architecture Is Still Valid

Even though the implementation changed from MySQL-centered planning to Supabase-centered execution, the project still satisfies the spirit of the original design goals:

- it remains modular
- it remains web-based
- it still uses Flask as the application layer
- it still provides peer-to-peer skill exchange
- it still supports both direct swap and time-credit models
- it still preserves a layered architecture
- it now has a more practical cloud deployment path than the original local-first approach

In other words, the implementation changed platforms and details, but it did not abandon the original problem statement or product intent.

## Summary Of The Most Important Project-Level Changes

1. The database strategy changed from MySQL planning to Supabase Postgres execution.
2. Authentication changed from local password verification to Supabase Auth with Flask session wrapping.
3. The credit system moved from concept to real ledger-based settlement with welcome credits.
4. Matching evolved from simple overlap logic to weighted marketplace recommendations.
5. Session handling became a real state machine with role-sensitive actions.
6. The UI evolved from wireframe-style templates to a more legitimate public marketplace experience.
7. The deployment target became Render, making the system externally reachable and production-oriented.

## Recommended Use Of This Document

This document can be used:
- as the follow-up narrative after the original design documents
- as evidence of implementation-driven architectural evolution
- as a maintainer guide for understanding why the live code differs from the initial academic plan
- as the starting point for a final technical report or post-implementation review

## Related Files In The Current Repo
- [README.md](/D:/APPS/Skill-bridge/README.md)
- [architecture.md](/D:/APPS/Skill-bridge/architecture.md)
- [security.md](/D:/APPS/Skill-bridge/security.md)
- [app/auth.py](/D:/APPS/Skill-bridge/app/auth.py)
- [app/domain.py](/D:/APPS/Skill-bridge/app/domain.py)
- [app/exchange.py](/D:/APPS/Skill-bridge/app/exchange.py)
- [db/schema.sql](/D:/APPS/Skill-bridge/db/schema.sql)

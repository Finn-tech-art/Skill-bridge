# SkillBridge

SkillBridge is a Flask + Supabase web app for peer-to-peer skill exchange. Students create profiles, list skills they can teach, add skills they want to learn, discover ranked matches, request exchange sessions, and settle time-credit exchanges after both sides confirm completion.

## Current Stack
- Flask
- Jinja templates
- Flask-Login
- Supabase Auth
- Supabase Postgres
- Gunicorn
- Render

## Core Features
- Email/password signup and login through Supabase Auth
- Local student profiles linked to Supabase auth identities
- Skill offers and learning goals
- Weighted match recommendations
- Exchange request lifecycle
- Credit ledger with welcome credits and session settlement
- Review flow for completed sessions

## Local Setup

### 1. Create a virtual environment
```bash
python -m venv .venv
```

### 2. Activate it
Windows:
```bash
.venv\Scripts\activate
```

macOS/Linux:
```bash
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
Copy `.env.example` to `.env` and set:

```env
SECRET_KEY=replace-with-a-long-random-secret
FLASK_ENV=development
FLASK_DEBUG=1
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your-supabase-anon-or-publishable-key
APP_BASE_URL=http://127.0.0.1:5000
```

### 5. Apply the auth migration in Supabase
Run [scripts/supabase_auth_migration.sql](/D:/APPS/Skill-bridge/scripts/supabase_auth_migration.sql) in the Supabase SQL editor.

### 6. Run the app
```bash
python run.py
```

Visit `http://127.0.0.1:5000`.

## Supabase Setup

In the Supabase dashboard:
1. Enable the `Email` auth provider.
2. Set your local dev redirect target, for example `http://127.0.0.1:5000`.
3. Configure your production Render URL later after deployment.
4. Ensure the `users` table has the `auth_user_id` column from the migration script.

## Render Deployment

This repo is prepared for Render with:
- [render.yaml](/D:/APPS/Skill-bridge/render.yaml)
- [Procfile](/D:/APPS/Skill-bridge/Procfile)
- health check at `/healthz`
- Gunicorn entrypoint `run:app`

### Render environment variables
Set these in Render:
- `SECRET_KEY`
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `FLASK_ENV=production`
- `FLASK_DEBUG=0`

### Deploy flow
1. Push this repo to GitHub.
2. Create a new Render Web Service from the repo.
3. Let Render use `render.yaml` or set:
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn run:app`
4. Add the environment variables above.
5. After the service is live, set the Render domain in Supabase Auth redirect settings.

## Testing
```bash
.venv\Scripts\python.exe -m pytest
```

## Project Files
- [architecture.md](/D:/APPS/Skill-bridge/architecture.md)
- [security.md](/D:/APPS/Skill-bridge/security.md)
- [db/schema.sql](/D:/APPS/Skill-bridge/db/schema.sql)
- [scripts/supabase_auth_migration.sql](/D:/APPS/Skill-bridge/scripts/supabase_auth_migration.sql)

## Next Recommended Improvements
1. Add CSRF protection.
2. Add Supabase RLS policies and document them.
3. Add route-level tests for the new auth and skill-management flows.
4. Add a Render deployment checklist for post-deploy verification.

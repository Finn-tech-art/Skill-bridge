# SkillBridge

A web-based peer-to-peer skill exchange platform for university students. SkillBridge enables students to share their skills, find skill matches, and exchange knowledge through a hybrid credit-based and direct-swap system.

## Project Overview

**SkillBridge** is a 12-week Agile project developed by **BIT 2221 Group 5** at **Multimedia University of Kenya**.

### Core Features
- **User Authentication**: Secure registration and login with hashed passwords
- **Skill Listing**: Post skills you can teach (offer) and skills you want to learn (want)
- **Skill Matching**: Intelligent matching engine that ranks candidates by category match, skill relevance, and reputation
- **Hybrid Exchange Model**: Exchange skills via time credits or direct skill swaps
- **Feedback & Rating**: Rate peers after completed sessions with 1–5 star reviews
- **Dashboard**: Track credit balance, reputation score, active sessions, and top matches
- **Session Management**: Request, confirm, and complete skill exchange sessions

## Tech Stack

- **Backend**: Python 3.10+, Flask 2.3.3
- **Database**: MySQL 8.x on Aiven Cloud (free tier available)
- **Frontend**: HTML5, Bootstrap 5, JavaScript
- **Hosting**: Aiven (MySQL), Aiven or Railway.app (Flask backend)
- **Version Control**: Git / GitHub
- **Testing**: pytest, pytest-cov
- **Code Quality**: Flake8, Black

## Project Structure

```
src/
├── app/                    # Flask application modules
│   ├── __init__.py        # App factory
│   ├── auth.py            # Authentication & user management
│   ├── skills.py          # Skill listing & browsing
│   ├── exchange.py        # Session & credit management
│   └── feedback.py        # Reviews & reputation
├── db/                     # Database
│   └── schema.sql         # MySQL schema & seed data
├── static/                 # Static files
│   ├── css/               # Stylesheets
│   └── js/                # JavaScript
├── templates/              # Jinja2 HTML templates
│   ├── base.html          # Base template
│   ├── auth/              # Authentication pages
│   ├── skills/            # Skill pages
│   ├── exchange/          # Session pages
│   └── feedback/          # Review pages
├── tests/                  # Test suite
│   ├── __init__.py
│   └── test_auth.py       # Authentication tests
├── config.py              # Configuration
├── run.py                 # Entry point
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Getting Started

### Prerequisites
- Python 3.10+
- Aiven Cloud MySQL database (free tier available)
- pip
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd src
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # macOS/Linux
   # or
   venv\Scripts\activate  # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up Aiven Cloud MySQL Database**
   
   For detailed step-by-step instructions, see [AIVEN_SETUP.md](AIVEN_SETUP.md).
   
   **Quick Summary:**
   - Sign up at [aiven.io](https://console.aiven.io) (free tier available)
   - Create a MySQL service
   - Note the connection details (host, port, username, password)
   - These will be used in Step 5

5. **Set up environment configuration**
   
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   
   - Edit `.env` with your Aiven credentials:
     ```
     SECRET_KEY=your-very-secret-key-at-least-32-chars
     MYSQL_HOST=mysql.c.skillbridge.aivencloud.com
     MYSQL_USER=avnadmin
     MYSQL_PASSWORD=your-aiven-password
     MYSQL_DB=defaultdb
     MYSQL_PORT=21513
     MYSQL_USE_SSL=true
     FLASK_ENV=development
     FLASK_DEBUG=1
     ```

6. **Download SSL Certificate (Optional but Recommended)**
   
   For secure connections to Aiven:
   ```bash
   # Download from Aiven console or use:
   openssl s_client -connect mysql.c.skillbridge.aivencloud.com:21513 -showcerts </dev/null 2>/dev/null | openssl x509 -outform PEM > ca.pem
   ```

7. **Initialize the database**
   
   ```bash
   # Option A: Using mysql client
   mysql -h mysql.c.skillbridge.aivencloud.com -P 21513 -u avnadmin -p < db/schema.sql
   
   # Option B: Using Python script (coming in Sprint 1)
   python scripts/init_db.py
   ```

8. **Run the application**
   ```bash
   python run.py
   ```
   
   Visit `http://localhost:5000` in your browser.

### Running Tests

```bash
pytest
# With coverage
pytest --cov=app tests/
```

## Aiven Cloud Database Management

### Accessing Your Database

**From Command Line:**
```bash
# Using mysql client
mysql -h mysql.c.skillbridge.aivencloud.com -P 21513 -u avnadmin -p defaultdb

# List all tables
SHOW TABLES;

# Check current connections
SHOW PROCESSLIST;
```

**From Aiven Console:**
- Log in to [console.aiven.io](https://console.aiven.io)
- Navigate to your MySQL service
- Use the **Databases** tab to manage databases
- Use the **Users** tab to reset passwords or add users
- View **Connection Info** for connection parameters

### Backing Up Data

```bash
# Full database dump
mysqldump -h mysql.c.skillbridge.aivencloud.com -P 21513 -u avnadmin -p defaultdb > backup.sql

# Restore from backup
mysql -h mysql.c.skillbridge.aivencloud.com -P 21513 -u avnadmin -p defaultdb < backup.sql
```

### Monitoring

- **Connection Limits**: Aiven free tier: 20 concurrent connections
- **Storage**: Free tier: 20 GB
- **Backups**: Aiven automatically backs up to 7 days
- **Metrics**: View in Aiven console under **Metrics** tab

## API Routes

### Authentication
- `GET /auth/register` - Show registration form
- `POST /auth/register` - Submit registration
- `GET /auth/login` - Show login form
- `POST /auth/login` - Submit login
- `GET /auth/logout` - Logout
- `GET /auth/profile` - View profile
- `POST /auth/profile/edit` - Edit profile

### Skills
- `GET /skills/my` - List your skills
- `POST /skills/add` - Add a skill
- `POST /skills/delete/<id>` - Delete a skill
- `GET /skills/browse` - Browse all skills
- `GET /skills/<id>` - View skill detail

### Exchange (Sprint 3+)
- `GET /exchange/sessions` - View your sessions
- `GET /exchange/credits/history` - View credit history

### Feedback (Sprint 4+)
- `GET /feedback/reviews` - View reviews received

## Development Workflow

1. Create a feature branch: `git checkout -b feature/task-name`
2. Make changes and test locally
3. Commit with descriptive messages: `git commit -m "Add feature description"`
4. Push to GitHub: `git push origin feature/task-name`
5. Create a Pull Request for review
6. Merge after approval

## Team Roles

- **DB & Backend Leads** (2): Schema design, matching engine, credit system
- **Backend Developers** (3): Auth, skills, exchange, feedback routes
- **Frontend Developers** (3): Templates, UI, forms, dashboard
- **QA / Tester** (1): Testing, usability studies, documentation
- **PM / Documentation** (1): GitHub management, coordination, reports

## Definition of Done

A task is "Done" when:
1. Code is committed and Pull Request is approved
2. Feature works in a fresh browser session
3. No hardcoded credentials or debug statements remain
4. Updated routes appear in API documentation
5. Database schema.sql is updated if needed
6. All tests pass

## Sprint Timeline

| Sprint | Weeks | Focus |
|--------|-------|-------|
| Sprint 0 | W1–W2 | Foundation & setup |
| Sprint 1 | W3–W4 | Authentication |
| Sprint 2 | W5–W6 | Skill listing & browse |
| Sprint 3 | W7–W8 | Matching & exchange |
| Sprint 4 | W9–W10 | Feedback & dashboard |
| Sprint 5 | W11–W12 | Testing & submission |

## Documentation

- Project proposal: See `.../docs/BIT 2221 GROUP 5 Main Proposal.docx`
- Wireframes: `/docs/wireframes.md` (to be added)
- API documentation: `/docs/API.md` (to be added)

## Support

For questions or issues, contact the PM or raise an issue on GitHub.

## License

This project is for educational purposes as part of the BIT 2221 course at Multimedia University of Kenya.

---

**Last Updated**: May 2024  
**Version**: 1.0.0 (Sprint 0 - Foundation)

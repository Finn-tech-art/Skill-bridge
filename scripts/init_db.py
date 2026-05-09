"""
SkillBridge — Aiven MySQL Database Initialiser
================================================
Usage:
    1. Fill in your Aiven credentials below (or set them as environment variables).
    2. Run:  python scripts/init_db.py
    3. The script creates all tables and seeds 5 demo users + 15 demo skills.

Aiven credentials are found in the Aiven Console → Your Service → Connection Information.
"""

import os
import sys
import mysql.connector
from mysql.connector import errorcode
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random
import string

# ─── CONFIGURATION ────────────────────────────────────────────────────────────
# Prefer environment variables; fall back to the literals below.
# Never commit real credentials to Git — use a .env file + python-dotenv instead.

DB_CONFIG = {
    "host":     os.getenv("MYSQL_HOST",     "your-service.aivencloud.com"),
    "port":     int(os.getenv("MYSQL_PORT", "12345")),        # Aiven uses a non-standard port
    "user":     os.getenv("MYSQL_USER",     "avnadmin"),
    "password": os.getenv("MYSQL_PASSWORD", "your-password"),
    "database": os.getenv("MYSQL_DB",       "defaultdb"),
    "ssl_ca":   os.getenv("MYSQL_SSL_CA",   "ca.pem"),        # Download from Aiven Console
    "ssl_disabled": False,
}

# ─── SQL — TABLE DEFINITIONS ──────────────────────────────────────────────────

TABLES = {}

TABLES["users"] = """
CREATE TABLE IF NOT EXISTS users (
    user_id         INT             AUTO_INCREMENT PRIMARY KEY,
    alias           VARCHAR(40)     NOT NULL UNIQUE,
    student_number  VARCHAR(20)     NOT NULL UNIQUE,
    password_hash   VARCHAR(255)    NOT NULL,
    school          VARCHAR(100)    DEFAULT NULL,
    year_of_study   TINYINT         DEFAULT NULL,
    credit_balance  INT             NOT NULL DEFAULT 0,
    reputation_score DECIMAL(3,2)   NOT NULL DEFAULT 0.00,
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

TABLES["skills"] = """
CREATE TABLE IF NOT EXISTS skills (
    skill_id    INT             AUTO_INCREMENT PRIMARY KEY,
    user_id     INT             NOT NULL,
    skill_name  VARCHAR(100)    NOT NULL,
    category    ENUM(
                    'Tech',
                    'Creative',
                    'Academic',
                    'Language',
                    'Music',
                    'Other'
                ) NOT NULL DEFAULT 'Other',
    description TEXT,
    skill_type  ENUM('offer','want') NOT NULL,
    created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_skills_user FOREIGN KEY (user_id)
        REFERENCES users (user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

TABLES["sessions"] = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id              INT         AUTO_INCREMENT PRIMARY KEY,
    teacher_id              INT         NOT NULL,
    learner_id              INT         NOT NULL,
    skill_id                INT         NOT NULL,
    exchange_type           ENUM('credit','swap') NOT NULL,
    swap_skill_id           INT         DEFAULT NULL,
    scheduled_at            DATETIME    NOT NULL,
    status                  ENUM('pending','confirmed','completed','cancelled')
                            NOT NULL DEFAULT 'pending',
    confirmed_by_teacher    TINYINT(1)  NOT NULL DEFAULT 0,
    confirmed_by_learner    TINYINT(1)  NOT NULL DEFAULT 0,
    created_at              DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_sessions_teacher    FOREIGN KEY (teacher_id)
        REFERENCES users  (user_id)  ON DELETE CASCADE,
    CONSTRAINT fk_sessions_learner    FOREIGN KEY (learner_id)
        REFERENCES users  (user_id)  ON DELETE CASCADE,
    CONSTRAINT fk_sessions_skill      FOREIGN KEY (skill_id)
        REFERENCES skills (skill_id) ON DELETE CASCADE,
    CONSTRAINT fk_sessions_swap_skill FOREIGN KEY (swap_skill_id)
        REFERENCES skills (skill_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

TABLES["credit_transactions"] = """
CREATE TABLE IF NOT EXISTS credit_transactions (
    tx_id       INT         AUTO_INCREMENT PRIMARY KEY,
    user_id     INT         NOT NULL,
    session_id  INT         NOT NULL,
    amount      INT         NOT NULL COMMENT '+1 earned (teaching), -1 spent (learning)',
    created_at  DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_tx_user    FOREIGN KEY (user_id)    REFERENCES users    (user_id)    ON DELETE CASCADE,
    CONSTRAINT fk_tx_session FOREIGN KEY (session_id) REFERENCES sessions (session_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

TABLES["reviews"] = """
CREATE TABLE IF NOT EXISTS reviews (
    review_id   INT         AUTO_INCREMENT PRIMARY KEY,
    session_id  INT         NOT NULL,
    reviewer_id INT         NOT NULL,
    reviewee_id INT         NOT NULL,
    score       TINYINT     NOT NULL,
    comment     TEXT,
    created_at  DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_score    CHECK (score BETWEEN 1 AND 5),
    CONSTRAINT uq_one_review_per_session_reviewer UNIQUE (session_id, reviewer_id),
    CONSTRAINT fk_review_session  FOREIGN KEY (session_id)  REFERENCES sessions (session_id) ON DELETE CASCADE,
    CONSTRAINT fk_review_reviewer FOREIGN KEY (reviewer_id) REFERENCES users    (user_id)    ON DELETE CASCADE,
    CONSTRAINT fk_review_reviewee FOREIGN KEY (reviewee_id) REFERENCES users    (user_id)    ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

# Indexes added separately for clarity
INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_skills_user_id   ON skills  (user_id);",
    "CREATE INDEX IF NOT EXISTS idx_skills_type       ON skills  (skill_type);",
    "CREATE INDEX IF NOT EXISTS idx_skills_category   ON skills  (category);",
    "CREATE INDEX IF NOT EXISTS idx_sessions_teacher  ON sessions (teacher_id);",
    "CREATE INDEX IF NOT EXISTS idx_sessions_learner  ON sessions (learner_id);",
    "CREATE INDEX IF NOT EXISTS idx_sessions_status   ON sessions (status);",
    "CREATE INDEX IF NOT EXISTS idx_reviews_reviewee  ON reviews  (reviewee_id);",
    "CREATE INDEX IF NOT EXISTS idx_tx_user           ON credit_transactions (user_id);",
]

# Table creation order matters — respect foreign key dependencies
TABLE_ORDER = ["users", "skills", "sessions", "credit_transactions", "reviews"]


# ─── SEED DATA ────────────────────────────────────────────────────────────────

def _alias(suffix: str) -> str:
    return f"user_{suffix}"


SEED_USERS = [
    {
        "alias":          _alias("a1b2"),
        "student_number": "MMU/2022/001",
        "password":       "Demo@1234",
        "school":         "School of Computing and Information Technology",
        "year_of_study":  3,
        "credit_balance": 4,
        "reputation_score": 4.50,
    },
    {
        "alias":          _alias("c3d4"),
        "student_number": "MMU/2023/002",
        "password":       "Demo@1234",
        "school":         "School of Engineering",
        "year_of_study":  2,
        "credit_balance": 1,
        "reputation_score": 4.00,
    },
    {
        "alias":          _alias("e5f6"),
        "student_number": "MMU/2021/003",
        "password":       "Demo@1234",
        "school":         "School of Business",
        "year_of_study":  4,
        "credit_balance": 0,
        "reputation_score": 3.80,
    },
    {
        "alias":          _alias("g7h8"),
        "student_number": "MMU/2024/004",
        "password":       "Demo@1234",
        "school":         "School of Computing and Information Technology",
        "year_of_study":  1,
        "credit_balance": 2,
        "reputation_score": 0.00,
    },
    {
        "alias":          _alias("i9j0"),
        "student_number": "MMU/2022/005",
        "password":       "Demo@1234",
        "school":         "School of Media and Journalism",
        "year_of_study":  3,
        "credit_balance": 3,
        "reputation_score": 4.20,
    },
]

# Each tuple: (alias_suffix, skill_name, category, description, skill_type)
SEED_SKILLS = [
    # user_a1b2 — offers Python and UI design; wants public speaking
    ("a1b2", "Python Programming",    "Tech",     "Can teach Python from basics to Flask web development. Comfortable with OOP, APIs and MySQL integration.", "offer"),
    ("a1b2", "UI/UX Design",          "Creative", "Teaches wireframing, Figma prototyping and Bootstrap layout principles.", "offer"),
    ("a1b2", "Public Speaking",        "Academic", "Wants to improve confidence in presentations and debates.", "want"),

    # user_c3d4 — offers electronics; wants Python and graphic design
    ("c3d4", "Electronics & Circuits", "Tech",     "Can teach basic and intermediate circuit design, PCB layout and Arduino programming.", "offer"),
    ("c3d4", "Python Programming",    "Tech",     "Wants to learn Python, especially for data science and automation.", "want"),
    ("c3d4", "Graphic Design",         "Creative", "Wants to learn Photoshop and Illustrator for engineering presentations.", "want"),

    # user_e5f6 — offers accounting and public speaking; wants web dev
    ("e5f6", "Financial Accounting",  "Academic", "Teaches double-entry bookkeeping, financial statements and Excel for accounting.", "offer"),
    ("e5f6", "Public Speaking",        "Academic", "Can coach presentation delivery, structuring arguments and managing nerves.", "offer"),
    ("e5f6", "Web Development",        "Tech",     "Wants to build a simple website for a business idea — needs HTML/CSS/JS basics.", "want"),

    # user_g7h8 — offers guitar; wants accounting and Python
    ("g7h8", "Guitar (Acoustic)",      "Music",    "Teaches beginner to intermediate acoustic guitar — chords, strumming patterns and simple melodies.", "offer"),
    ("g7h8", "Financial Accounting",  "Academic", "Needs help understanding accounting concepts for a business unit.", "want"),
    ("g7h8", "Python Programming",    "Tech",     "Wants to learn Python to automate repetitive tasks.", "want"),

    # user_i9j0 — offers video editing and Swahili; wants guitar and UI design
    ("i9j0", "Video Editing",          "Creative", "Teaches Premiere Pro and DaVinci Resolve — cutting, colour grading and export for social media.", "offer"),
    ("i9j0", "Swahili Language",       "Language", "Native Swahili speaker. Can teach conversational Swahili and grammar.", "offer"),
    ("i9j0", "Guitar (Acoustic)",      "Music",    "Wants to pick up acoustic guitar as a hobby.", "want"),
    ("i9j0", "UI/UX Design",          "Creative", "Wants to design better thumbnails and video graphics.", "want"),
]


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def get_connection():
    """Open a connection to the Aiven MySQL instance."""
    cfg = {k: v for k, v in DB_CONFIG.items() if v}  # drop empty values
    # If the ssl_ca file doesn't exist locally, skip SSL (not recommended for production)
    if cfg.get("ssl_ca") and not os.path.exists(cfg["ssl_ca"]):
        print(f"  ⚠  SSL CA file '{cfg['ssl_ca']}' not found — connecting without SSL.")
        print("     Download it from Aiven Console → your service → Connection Information → CA Certificate.")
        cfg.pop("ssl_ca", None)
        cfg["ssl_disabled"] = True
    return mysql.connector.connect(**cfg)


def run_sql(cursor, sql: str, label: str = ""):
    """Execute a single SQL statement and print result."""
    try:
        cursor.execute(sql)
        print(f"  ✓  {label or sql[:60].strip()}")
    except mysql.connector.Error as e:
        if e.errno == errorcode.ER_TABLE_EXISTS_ERROR:
            print(f"  –  {label} already exists, skipped.")
        else:
            raise


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def create_tables(cursor):
    print("\n📦  Creating tables...")
    for name in TABLE_ORDER:
        run_sql(cursor, TABLES[name], f"Table `{name}`")


def create_indexes(cursor):
    print("\n🔍  Creating indexes...")
    for idx_sql in INDEXES:
        label = idx_sql.split("ON ")[1].strip().rstrip(";")
        try:
            cursor.execute(idx_sql)
            print(f"  ✓  Index on {label}")
        except mysql.connector.Error as e:
            # Older MySQL versions don't support IF NOT EXISTS on CREATE INDEX
            if e.errno == 1061:  # Duplicate key name
                print(f"  –  Index on {label} already exists, skipped.")
            else:
                raise


def seed_users(cursor) -> dict:
    """Insert demo users and return a mapping of alias_suffix -> user_id."""
    print("\n👤  Seeding demo users...")
    alias_to_id = {}
    sql = """
        INSERT IGNORE INTO users
            (alias, student_number, password_hash, school, year_of_study, credit_balance, reputation_score)
        VALUES
            (%s, %s, %s, %s, %s, %s, %s)
    """
    for u in SEED_USERS:
        hashed = generate_password_hash(u["password"])
        cursor.execute(sql, (
            u["alias"], u["student_number"], hashed,
            u["school"], u["year_of_study"],
            u["credit_balance"], u["reputation_score"]
        ))
        # Fetch the user_id (works even if row already existed via IGNORE)
        cursor.execute("SELECT user_id FROM users WHERE alias = %s", (u["alias"],))
        row = cursor.fetchone()
        suffix = u["alias"].split("_")[1]
        alias_to_id[suffix] = row[0]
        print(f"  ✓  {u['alias']} (student: {u['student_number']}, id: {row[0]})")
    return alias_to_id


def seed_skills(cursor, alias_to_id: dict):
    """Insert demo skills linked to the seeded users."""
    print("\n🎓  Seeding demo skills...")
    sql = """
        INSERT IGNORE INTO skills (user_id, skill_name, category, description, skill_type)
        VALUES (%s, %s, %s, %s, %s)
    """
    for suffix, skill_name, category, description, skill_type in SEED_SKILLS:
        user_id = alias_to_id.get(suffix)
        if not user_id:
            print(f"  ✗  Alias suffix '{suffix}' not found — skipping skill '{skill_name}'")
            continue
        cursor.execute(sql, (user_id, skill_name, category, description, skill_type))
        print(f"  ✓  [{skill_type.upper():5s}] {skill_name} → user_{suffix}")


def verify(cursor):
    """Print row counts for all tables as a quick sanity check."""
    print("\n✅  Verification — row counts:")
    for table in TABLE_ORDER:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"     {table:<25} {count:>3} rows")


def main():
    print("=" * 60)
    print("  SkillBridge — Aiven DB Initialiser")
    print("=" * 60)
    print(f"\n🔗  Connecting to {DB_CONFIG['host']}:{DB_CONFIG['port']} ...")

    try:
        conn = get_connection()
    except mysql.connector.Error as e:
        print(f"\n❌  Connection failed: {e}")
        print("\n💡  Check your credentials in DB_CONFIG or environment variables.")
        print("    Make sure you have downloaded ca.pem from the Aiven Console.\n")
        sys.exit(1)

    print("  ✓  Connected successfully.\n")

    cursor = conn.cursor()

    try:
        create_tables(cursor)
        create_indexes(cursor)
        alias_to_id = seed_users(cursor)
        seed_skills(cursor, alias_to_id)
        conn.commit()
        verify(cursor)
        print("\n🎉  Database initialised successfully!")
        print("    All demo passwords are:  Demo@1234\n")

    except mysql.connector.Error as e:
        conn.rollback()
        print(f"\n❌  Error during initialisation: {e}")
        sys.exit(1)

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
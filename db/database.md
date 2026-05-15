# SkillBridge Database Design Documentation

## 1. Overview

The SkillBridge system uses a cloud-hosted PostgreSQL database provided through Supabase. The database is designed to support a hybrid peer-to-peer skill exchange platform for university students, enabling structured learning through both time-credit exchanges and direct skill swaps.

The database follows a fully relational design, ensuring data integrity, scalability, and auditability of all peer learning interactions.

---

## 2. Database Technology

- Database System: PostgreSQL (via Supabase)
- Access Layer: Supabase Python Client (Flask backend integration)
- Architecture: API-driven (Flask → Supabase → PostgreSQL)
- Timestamp Standard: TIMESTAMPTZ (timezone-aware)

---

## 3. Design Principles

The schema is guided by the following principles:

### 3.1 Normalization
Data is structured to reduce redundancy by separating:
- Users
- Skills catalogue
- Skill offerings
- Skill requests
- Sessions
- Credit transactions
- Reviews

### 3.2 Transaction Integrity
All learning exchanges are recorded through immutable session and credit transaction records.

### 3.3 Auditability
Every credit movement is logged in a transaction ledger for transparency.

### 3.4 Scalability
The schema supports future expansion into recommendation systems and analytics.

---

## 4. Entity Relationship Overview

### Core Entities:

- users
- skills
- user_skill_offers
- user_skill_wants
- exchange_sessions
- credit_transactions
- reviews

---

## 5. Entity Descriptions

### 5.1 Users
Stores student identity and profile information.

**Key Attributes:**
- id (PK)
- student_number (unique)
- registration_number (unique)
- email (unique)
- password_hash
- department, year_of_study
- bio, avatar_url
- created_at, updated_at

**Relationships:**
- One user → many skill offers
- One user → many skill requests
- One user → many sessions (as requester/provider)
- One user → many reviews

---

### 5.2 Skills (Catalogue)
Central list of all skills available in the system.

**Attributes:**
- id (PK)
- name (unique)
- slug (unique)
- description

---

### 5.3 User Skill Offers
Represents skills a user can teach.

**Attributes:**
- user_id (FK → users)
- skill_id (FK → skills)
- proficiency_level
- description

**Constraints:**
- Unique (user_id, skill_id)

---

### 5.4 User Skill Wants
Represents skills a user wants to learn.

**Attributes:**
- user_id (FK → users)
- skill_id (FK → skills)
- priority
- notes

**Constraints:**
- Unique (user_id, skill_id)

---

### 5.5 Exchange Sessions
Represents a learning transaction between two users.

**Attributes:**
- requester_id (FK → users)
- provider_id (FK → users)
- requester_skill_id (FK → skills)
- provider_skill_id (FK → skills)
- exchange_type (time_credit | direct_swap)
- status (pending, accepted, completed, cancelled, disputed)
- scheduled_start, scheduled_end
- duration_minutes
- confirmation flags

**Constraints:**
- requester_id ≠ provider_id

---

### 5.6 Credit Transactions
Ledger system for time-credit economy.

**Attributes:**
- user_id (FK → users)
- session_id (FK → exchange_sessions)
- amount (+/-)
- balance_after
- transaction_type (earned, spent, adjustment)

---

### 5.7 Reviews
Feedback system for trust and quality control.

**Attributes:**
- session_id (FK → sessions)
- reviewer_id
- reviewee_id
- rating (1–5)
- comment

**Constraints:**
- reviewer_id ≠ reviewee_id
- One review per session pair

---

## 6. Timestamp Strategy

All tables use:

- created_at TIMESTAMPTZ DEFAULT NOW()
- updated_at TIMESTAMPTZ DEFAULT NOW()

This ensures timezone consistency in cloud deployment.

---

## 7. Summary

The SkillBridge database is designed as a relational, cloud-native system optimized for peer-to-peer learning workflows. It supports structured skill exchange, financial-like credit tracking, and trust-based reputation scoring, making it suitable for scalable deployment in university environments.
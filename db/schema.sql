-- =====================================================
-- SkillBridge PostgreSQL Schema (Supabase)
-- =====================================================

-- USERS
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    auth_user_id UUID UNIQUE,

    full_name VARCHAR(150) NOT NULL,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,

    password_hash VARCHAR(255),

    year_of_study SMALLINT,
    department VARCHAR(150),
    bio TEXT,
    avatar_url VARCHAR(255),
    preferred_contact_method TEXT CHECK (
        preferred_contact_method IN ('phone', 'email', 'instagram')
    ),
    contact_phone VARCHAR(30),
    contact_email VARCHAR(255),
    instagram_handle VARCHAR(100),

    is_active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- SKILLS CATALOGUE
CREATE TABLE skills (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(120) UNIQUE NOT NULL,
    slug VARCHAR(140) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- USER SKILL OFFERS
CREATE TABLE user_skill_offers (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    skill_id BIGINT REFERENCES skills(id) ON DELETE RESTRICT,

    proficiency_level TEXT CHECK (
        proficiency_level IN ('beginner', 'intermediate', 'advanced', 'expert')
    ) DEFAULT 'intermediate',

    description VARCHAR(500),
    is_verified BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(user_id, skill_id)
);

-- USER SKILL WANTS
CREATE TABLE user_skill_wants (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    skill_id BIGINT REFERENCES skills(id) ON DELETE RESTRICT,

    priority SMALLINT DEFAULT 1,
    notes VARCHAR(500),

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(user_id, skill_id)
);

-- EXCHANGE SESSIONS
CREATE TABLE exchange_sessions (
    id BIGSERIAL PRIMARY KEY,

    requester_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    provider_id BIGINT REFERENCES users(id) ON DELETE CASCADE,

    requester_skill_id BIGINT REFERENCES skills(id),
    provider_skill_id BIGINT REFERENCES skills(id),

    exchange_type TEXT CHECK (
        exchange_type IN ('time_credit', 'direct_swap')
    ) NOT NULL,

    scheduled_start TIMESTAMPTZ,
    scheduled_end TIMESTAMPTZ,
    duration_minutes INT DEFAULT 60,

    location VARCHAR(255),
    meeting_link VARCHAR(255),

    status TEXT DEFAULT 'pending' CHECK (
        status IN ('pending', 'accepted', 'rejected', 'cancelled', 'completed', 'disputed')
    ),

    requester_confirmed BOOLEAN DEFAULT FALSE,
    provider_confirmed BOOLEAN DEFAULT FALSE,

    requester_notes VARCHAR(500),
    provider_notes VARCHAR(500),

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    CHECK (requester_id <> provider_id),
    CHECK (duration_minutes > 0)
);

-- CREDIT TRANSACTIONS
CREATE TABLE credit_transactions (
    id BIGSERIAL PRIMARY KEY,

    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    session_id BIGINT REFERENCES exchange_sessions(id) ON DELETE SET NULL,

    amount NUMERIC(10,2) NOT NULL,
    balance_after NUMERIC(10,2) NOT NULL,

    transaction_type TEXT CHECK (
        transaction_type IN ('earned', 'spent', 'adjustment')
    ) NOT NULL,

    reference_note VARCHAR(255),

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- REVIEWS
CREATE TABLE reviews (
    id BIGSERIAL PRIMARY KEY,

    session_id BIGINT REFERENCES exchange_sessions(id) ON DELETE CASCADE,

    reviewer_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    reviewee_id BIGINT REFERENCES users(id) ON DELETE CASCADE,

    rating SMALLINT CHECK (rating BETWEEN 1 AND 5),
    comment VARCHAR(1000),

    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(session_id, reviewer_id, reviewee_id),
    CHECK (reviewer_id <> reviewee_id)
);

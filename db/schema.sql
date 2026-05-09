-- SkillBridge Database Schema
-- MySQL 8.x

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    alias VARCHAR(40) UNIQUE NOT NULL,
    student_number VARCHAR(20) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    school VARCHAR(100),
    year_of_study TINYINT,
    credit_balance INT DEFAULT 0,
    reputation_score DECIMAL(3,2) DEFAULT 0.00,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_alias (alias),
    INDEX idx_student_number (student_number)
);

-- Create skills table
CREATE TABLE IF NOT EXISTS skills (
    skill_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    skill_name VARCHAR(100) NOT NULL,
    category VARCHAR(60),
    description TEXT,
    skill_type ENUM('offer', 'want') NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_skill_type (skill_type),
    INDEX idx_category (category)
);

-- Create sessions table
CREATE TABLE IF NOT EXISTS sessions (
    session_id INT PRIMARY KEY AUTO_INCREMENT,
    teacher_id INT NOT NULL,
    learner_id INT NOT NULL,
    skill_id INT NOT NULL,
    exchange_type ENUM('credit', 'swap') NOT NULL,
    swap_skill_id INT,
    scheduled_at DATETIME,
    status ENUM('pending', 'confirmed', 'completed', 'cancelled') DEFAULT 'pending',
    confirmed_by_teacher TINYINT(1) DEFAULT 0,
    confirmed_by_learner TINYINT(1) DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (teacher_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (learner_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (skill_id) REFERENCES skills(skill_id) ON DELETE CASCADE,
    FOREIGN KEY (swap_skill_id) REFERENCES skills(skill_id) ON DELETE SET NULL,
    INDEX idx_teacher_id (teacher_id),
    INDEX idx_learner_id (learner_id),
    INDEX idx_status (status)
);

-- Create credit_transactions table
CREATE TABLE IF NOT EXISTS credit_transactions (
    tx_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    session_id INT NOT NULL,
    amount INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
);

-- Create reviews table
CREATE TABLE IF NOT EXISTS reviews (
    review_id INT PRIMARY KEY AUTO_INCREMENT,
    session_id INT NOT NULL,
    reviewer_id INT NOT NULL,
    reviewee_id INT NOT NULL,
    score TINYINT CHECK (score BETWEEN 1 AND 5) NOT NULL,
    comment TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
    FOREIGN KEY (reviewer_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (reviewee_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE KEY unique_review (session_id, reviewer_id),
    INDEX idx_reviewee_id (reviewee_id)
);

-- Seed data: 5 demo users
INSERT INTO users (alias, student_number, password_hash, school, year_of_study, credit_balance, reputation_score)
VALUES
    ('user_a1b2', 'STU001', 'pbkdf2:sha256:600000$demo001$hash1', 'School of IT', 2, 5, 4.5),
    ('user_c3d4', 'STU002', 'pbkdf2:sha256:600000$demo002$hash2', 'School of Design', 3, 3, 4.0),
    ('user_e5f6', 'STU003', 'pbkdf2:sha256:600000$demo003$hash3', 'School of Business', 1, 0, 3.8),
    ('user_g7h8', 'STU004', 'pbkdf2:sha256:600000$demo004$hash4', 'School of Languages', 2, 7, 4.2),
    ('user_i9j0', 'STU005', 'pbkdf2:sha256:600000$demo005$hash5', 'School of Music', 3, 2, 3.9);

-- Seed data: 10 demo skills
INSERT INTO skills (user_id, skill_name, category, description, skill_type)
VALUES
    (1, 'Python Programming', 'Tech', 'Learn Python basics and advanced concepts', 'offer'),
    (1, 'Web Design', 'Creative', 'Looking to learn modern web design principles', 'want'),
    (2, 'Graphic Design', 'Creative', 'Professional graphic design for print and digital', 'offer'),
    (2, 'Data Analysis', 'Tech', 'Interested in learning data analysis with Excel', 'want'),
    (3, 'Public Speaking', 'Academic', 'Improve your presentation and speaking skills', 'offer'),
    (3, 'French Language', 'Language', 'Beginner French language learner', 'want'),
    (4, 'Spanish Conversation', 'Language', 'Fluent Spanish speaker offering conversation practice', 'offer'),
    (4, 'Music Production', 'Music', 'Want to learn music production basics', 'want'),
    (5, 'Piano Lessons', 'Music', 'Experienced piano teacher', 'offer'),
    (5, 'JavaScript', 'Tech', 'Looking to master JavaScript', 'want');

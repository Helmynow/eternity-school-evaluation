-- Initial Schema Migration for Eternity School Evaluation System
-- Creates all tables, enums, indexes, and constraints

-- ============================================================================
-- ENUMS
-- ============================================================================

-- Create enums only if they don't exist
DO $$ BEGIN
    CREATE TYPE staff_segment AS ENUM ('national', 'international', 'whole_school');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE eom_category AS ENUM ('academic', 'admin', 'support', 'leadership', 'innovation', 'collaboration', 'student_engagement');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE action_type AS ENUM ('create', 'update', 'delete', 'submit', 'approve', 'reject', 'view', 'export');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE rotation_period_type AS ENUM ('year', 'quarter', 'month', 'term');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- Cycles table
CREATE TABLE IF NOT EXISTS cycles (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    start_date DATE,
    end_date DATE,
    status VARCHAR(20) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cycles_code ON cycles(code);
CREATE INDEX IF NOT EXISTS idx_cycles_status ON cycles(status);

-- People table (Staff)
CREATE TABLE IF NOT EXISTS people (
    email VARCHAR(255) PRIMARY KEY,
    full_name VARCHAR(200) NOT NULL,
    role_title VARCHAR(100),
    department VARCHAR(100),
    segment staff_segment NOT NULL DEFAULT 'whole_school',
    hire_date DATE,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes only if columns exist (handled in migration 20240101000004)
-- CREATE INDEX IF NOT EXISTS idx_person_segment ON people(segment);
-- CREATE INDEX IF NOT EXISTS idx_person_active ON people(active);
-- CREATE INDEX IF NOT EXISTS idx_person_department ON people(department);

-- Weight Matrices table
CREATE TABLE IF NOT EXISTS weight_matrices (
    id SERIAL PRIMARY KEY,
    cycle_id INTEGER REFERENCES cycles(id) ON DELETE CASCADE,
    name VARCHAR(200),
    description TEXT,
    matrix_config JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_weight_matrix_cycle ON weight_matrices(cycle_id);
CREATE INDEX IF NOT EXISTS idx_weight_matrix_active ON weight_matrices(is_active);

-- Assignments table (MRE)
CREATE TABLE IF NOT EXISTS assignments (
    id SERIAL PRIMARY KEY,
    cycle_id INTEGER NOT NULL REFERENCES cycles(id) ON DELETE CASCADE,
    rater_email VARCHAR(255) NOT NULL REFERENCES people(email) ON DELETE CASCADE,
    rater_role VARCHAR(100),
    target_email VARCHAR(255) NOT NULL REFERENCES people(email) ON DELETE CASCADE,
    target_role VARCHAR(100),
    target_group VARCHAR(50),
    rater_context VARCHAR(100),
    weight FLOAT DEFAULT 1.0,
    weight_matrix_id INTEGER REFERENCES weight_matrices(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_assignment_cycle ON assignments(cycle_id);
CREATE INDEX IF NOT EXISTS idx_assignment_rater ON assignments(rater_email);
CREATE INDEX IF NOT EXISTS idx_assignment_target ON assignments(target_email);
CREATE INDEX IF NOT EXISTS idx_assignment_context ON assignments(rater_context);
CREATE INDEX IF NOT EXISTS idx_assignment_target_group ON assignments(target_group);

-- Evaluations table
CREATE TABLE IF NOT EXISTS evaluations (
    id SERIAL PRIMARY KEY,
    assignment_id INTEGER NOT NULL REFERENCES assignments(id) ON DELETE CASCADE,
    rating FLOAT,
    feedback TEXT,
    status VARCHAR(20) DEFAULT 'draft',
    submitted_at TIMESTAMP,
    weighted_rating FLOAT,
    domain_scores JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_evaluation_assignment ON evaluations(assignment_id);
CREATE INDEX IF NOT EXISTS idx_evaluation_status ON evaluations(status);
CREATE INDEX IF NOT EXISTS idx_evaluation_submitted ON evaluations(submitted_at);

-- ============================================================================
-- EOM (Employee of the Month) TABLES
-- ============================================================================

-- EOM Cycles table
CREATE TABLE IF NOT EXISTS eom_cycles (
    id SERIAL PRIMARY KEY,
    cycle_id INTEGER NOT NULL REFERENCES cycles(id) ON DELETE CASCADE,
    month INTEGER NOT NULL,
    year INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'draft',
    category_rotation JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(cycle_id, month, year)
);

CREATE INDEX IF NOT EXISTS idx_eom_cycle_year_month ON eom_cycles(year, month);
CREATE INDEX IF NOT EXISTS idx_eom_cycle_status ON eom_cycles(status);

-- EOM Voters table
CREATE TABLE IF NOT EXISTS eom_voters (
    id SERIAL PRIMARY KEY,
    eom_cycle_id INTEGER NOT NULL REFERENCES eom_cycles(id) ON DELETE CASCADE,
    voter_email VARCHAR(255) NOT NULL REFERENCES people(email) ON DELETE CASCADE,
    UNIQUE(eom_cycle_id, voter_email)
);

CREATE INDEX IF NOT EXISTS idx_eom_voter_cycle ON eom_voters(eom_cycle_id);
CREATE INDEX IF NOT EXISTS idx_eom_voter_email ON eom_voters(voter_email);

-- EOM Nominees table
CREATE TABLE IF NOT EXISTS eom_nominees (
    id SERIAL PRIMARY KEY,
    eom_cycle_id INTEGER NOT NULL REFERENCES eom_cycles(id) ON DELETE CASCADE,
    nominee_email VARCHAR(255) NOT NULL REFERENCES people(email) ON DELETE CASCADE,
    nominated_by VARCHAR(255) REFERENCES people(email) ON DELETE SET NULL,
    nomination_reason TEXT,
    category eom_category NOT NULL,
    rotation_eligible BOOLEAN DEFAULT TRUE,
    last_nominated_cycle_id INTEGER REFERENCES eom_cycles(id) ON DELETE SET NULL,
    last_won_cycle_id INTEGER REFERENCES eom_cycles(id) ON DELETE SET NULL,
    nomination_count INTEGER DEFAULT 0,
    win_count INTEGER DEFAULT 0,
    votes_received INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(eom_cycle_id, nominee_email, category)
);

CREATE INDEX IF NOT EXISTS idx_eom_nominee_category ON eom_nominees(category);
CREATE INDEX IF NOT EXISTS idx_eom_nominee_rotation ON eom_nominees(rotation_eligible);
CREATE INDEX IF NOT EXISTS idx_eom_nominee_cycle ON eom_nominees(eom_cycle_id);
CREATE INDEX IF NOT EXISTS idx_eom_nominee_email ON eom_nominees(nominee_email);

-- EOM Winners table
CREATE TABLE IF NOT EXISTS eom_winners (
    id SERIAL PRIMARY KEY,
    eom_cycle_id INTEGER NOT NULL REFERENCES eom_cycles(id) ON DELETE CASCADE,
    winner_email VARCHAR(255) NOT NULL REFERENCES people(email) ON DELETE CASCADE,
    category VARCHAR(50),
    term VARCHAR(50),
    votes_received INTEGER,
    announced_at DATE DEFAULT CURRENT_DATE
);

CREATE INDEX IF NOT EXISTS idx_eom_winner_cycle ON eom_winners(eom_cycle_id);
CREATE INDEX IF NOT EXISTS idx_eom_winner_email ON eom_winners(winner_email);
CREATE INDEX IF NOT EXISTS idx_eom_winner_term ON eom_winners(term);

-- EOM Rotation Rules table
CREATE TABLE IF NOT EXISTS eom_rotation_rules (
    id SERIAL PRIMARY KEY,
    cycle_id INTEGER NOT NULL REFERENCES cycles(id) ON DELETE CASCADE,
    category eom_category NOT NULL,
    cooldown_period INTEGER DEFAULT 3,
    max_wins_per_period INTEGER DEFAULT 1,
    period_type rotation_period_type DEFAULT 'quarter',
    max_nominations_per_year INTEGER DEFAULT 2,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(cycle_id, category)
);

CREATE INDEX IF NOT EXISTS idx_rotation_rule_cycle ON eom_rotation_rules(cycle_id);
CREATE INDEX IF NOT EXISTS idx_rotation_rule_category ON eom_rotation_rules(category);
CREATE INDEX IF NOT EXISTS idx_rotation_rule_active ON eom_rotation_rules(is_active);

-- ============================================================================
-- AUDIT TRAIL
-- ============================================================================

-- Audit Log table
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    action_type action_type NOT NULL,
    entity_type VARCHAR(100),
    entity_id INTEGER,
    user_email VARCHAR(255) REFERENCES people(email) ON DELETE SET NULL,
    user_role VARCHAR(100),
    changes JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_logs(action_type);
CREATE INDEX IF NOT EXISTS idx_audit_log_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_user ON audit_logs(user_email);
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_logs(timestamp);

-- ============================================================================
-- TRIGGERS FOR UPDATED_AT
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_cycles_updated_at BEFORE UPDATE ON cycles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_people_updated_at BEFORE UPDATE ON people
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_assignments_updated_at BEFORE UPDATE ON assignments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_evaluations_updated_at BEFORE UPDATE ON evaluations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_eom_cycles_updated_at BEFORE UPDATE ON eom_cycles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_eom_nominees_updated_at BEFORE UPDATE ON eom_nominees
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_weight_matrices_updated_at BEFORE UPDATE ON weight_matrices
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_rotation_rules_updated_at BEFORE UPDATE ON eom_rotation_rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE cycles IS 'Evaluation cycles (e.g., Q1-2024, Annual-2024)';
COMMENT ON TABLE people IS 'Staff members with segment support';
COMMENT ON TABLE assignments IS 'MRE assignments: who evaluates whom';
COMMENT ON TABLE evaluations IS 'Individual evaluation submissions';
COMMENT ON TABLE eom_cycles IS 'Employee of the Month cycles';
COMMENT ON TABLE eom_nominees IS 'EOM nominees with rotation tracking';
COMMENT ON TABLE eom_winners IS 'EOM winners history';
COMMENT ON TABLE eom_rotation_rules IS 'Rotation rules for EOM categories';
COMMENT ON TABLE audit_logs IS 'Audit trail for all system actions';
COMMENT ON TABLE weight_matrices IS 'Weight matrix configurations for evaluation cycles';


-- Seed Data for Eternity School Evaluation System
-- Optional: Run this after migrations to populate initial data

-- ============================================================================
-- SAMPLE CYCLES
-- ============================================================================

INSERT INTO cycles (code, name, start_date, end_date, status) VALUES
('CYCLE-2024-Q1', '2024 Q1 Evaluation', '2024-01-01', '2024-03-31', 'active'),
('CYCLE-2024-Q2', '2024 Q2 Evaluation', '2024-04-01', '2024-06-30', 'active'),
('CYCLE-2024-Q3', '2024 Q3 Evaluation', '2024-07-01', '2024-09-30', 'draft'),
('CYCLE-2024-Q4', '2024 Q4 Evaluation', '2024-10-01', '2024-12-31', 'draft')
ON CONFLICT (code) DO NOTHING;

-- ============================================================================
-- SAMPLE PEOPLE (Staff)
-- ============================================================================

INSERT INTO people (email, full_name, role_title, department, segment, active) VALUES
-- Academic Staff
('teacher1@eternity.edu', 'John Teacher', 'Mathematics Teacher', 'Academics', 'national', TRUE),
('teacher2@eternity.edu', 'Jane Instructor', 'Science Teacher', 'Academics', 'international', TRUE),
('teacher3@eternity.edu', 'Bob Professor', 'English Teacher', 'Academics', 'whole_school', TRUE),
('teacher4@eternity.edu', 'Alice Lecturer', 'History Teacher', 'Academics', 'national', TRUE),
('teacher5@eternity.edu', 'Charlie Faculty', 'Art Teacher', 'Academics', 'international', TRUE),

-- Admin Staff
('admin1@eternity.edu', 'David Coordinator', 'Administrative Coordinator', 'Administration', 'whole_school', TRUE),
('admin2@eternity.edu', 'Eve Manager', 'Operations Manager', 'Administration', 'national', TRUE),
('admin3@eternity.edu', 'Frank Director', 'HR Director', 'Administration', 'international', TRUE),
('admin4@eternity.edu', 'Grace Secretary', 'Executive Secretary', 'Administration', 'whole_school', TRUE),

-- Leaders
('leader1@eternity.edu', 'Henry Principal', 'School Principal', 'Leadership', 'whole_school', TRUE),
('leader2@eternity.edu', 'Iris VP', 'Vice Principal', 'Leadership', 'national', TRUE),
('leader3@eternity.edu', 'Jack Head', 'Department Head', 'Leadership', 'international', TRUE)
ON CONFLICT (email) DO NOTHING;

-- ============================================================================
-- SAMPLE EOM CYCLES
-- ============================================================================

INSERT INTO eom_cycles (cycle_id, month, year, status)
SELECT 
    c.id,
    m.month,
    2024,
    CASE WHEN m.month <= EXTRACT(MONTH FROM CURRENT_DATE) THEN 'active' ELSE 'draft' END
FROM cycles c
CROSS JOIN generate_series(1, 12) AS m(month)
WHERE c.code = 'CYCLE-2024-Q1'
ON CONFLICT DO NOTHING;

-- ============================================================================
-- SAMPLE ROTATION RULES
-- ============================================================================

INSERT INTO eom_rotation_rules (cycle_id, category, cooldown_period, max_wins_per_period, period_type, max_nominations_per_year)
SELECT 
    c.id,
    cat.category,
    CASE cat.category
        WHEN 'academic' THEN 3
        WHEN 'admin' THEN 2
        WHEN 'leadership' THEN 6
        WHEN 'innovation' THEN 1
        ELSE 3
    END,
    1,
    CASE cat.category
        WHEN 'leadership' THEN 'year'
        WHEN 'innovation' THEN 'year'
        ELSE 'quarter'
    END,
    CASE cat.category
        WHEN 'leadership' THEN 1
        WHEN 'innovation' THEN 3
        ELSE 2
    END
FROM cycles c
CROSS JOIN (SELECT unnest(ARRAY['academic', 'admin', 'support', 'leadership', 'innovation', 'collaboration', 'student_engagement']::eom_category[]) AS category) cat
WHERE c.code = 'CYCLE-2024-Q1'
ON CONFLICT (cycle_id, category) DO NOTHING;

-- ============================================================================
-- SAMPLE WEIGHT MATRIX
-- ============================================================================

INSERT INTO weight_matrices (cycle_id, name, description, matrix_config, is_active)
SELECT 
    c.id,
    'Default Weight Matrix',
    'Default weight matrix for Eternity School evaluations',
    '{
        "academic": {
            "CEO": 1.0,
            "P&C": 0.8,
            "QA": 1.0,
            "peer_review": 0.9,
            "manager_review": 1.0,
            "direct_report_review": 0.7,
            "self_review": 0.5,
            "360_review": 0.85
        },
        "admin": {
            "CEO": 1.0,
            "P&C": 1.0,
            "QA": 0.7,
            "peer_review": 0.8,
            "manager_review": 1.0,
            "direct_report_review": 0.6,
            "self_review": 0.5,
            "360_review": 0.85
        }
    }'::jsonb,
    TRUE
FROM cycles c
WHERE c.code = 'CYCLE-2024-Q1'
ON CONFLICT DO NOTHING;


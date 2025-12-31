-- Create Reporting Views for Eternity School Evaluation System

-- ============================================================================
-- MRE REPORTING VIEWS
-- ============================================================================

-- 1) MRE: Who evaluates who (names + roles)
-- Note: Uses assignment roles (a.rater_role, a.target_role) which always exist
CREATE OR REPLACE VIEW mre_who_evaluates_who AS
SELECT
    cy.code          AS cycle_code,
    a.rater_email,
    pr.full_name     AS rater_name,
    a.rater_role AS rater_role,
    a.target_email,
    pt.full_name     AS target_name,
    a.target_role AS target_role,
    a.target_group,
    a.rater_context,
    a.weight,
    e.rating,
    e.status AS evaluation_status
FROM assignments a
JOIN cycles cy ON cy.id = a.cycle_id
LEFT JOIN people pr ON pr.email = a.rater_email
LEFT JOIN people pt ON pt.email = a.target_email
LEFT JOIN evaluations e ON e.assignment_id = a.id
ORDER BY cycle_code, a.target_group, a.rater_context, rater_name, target_name;

-- 2) MRE Evaluation Summary by Target
-- Note: Uses NULL for segment until column is added
CREATE OR REPLACE VIEW mre_evaluation_summary AS
SELECT
    cy.code AS cycle_code,
    a.target_email,
    pt.full_name AS target_name,
    NULL::staff_segment AS target_segment,  -- Will be populated once column exists
    COUNT(e.id) AS total_evaluations,
    COUNT(CASE WHEN e.status = 'submitted' THEN 1 END) AS submitted_evaluations,
    AVG(CASE WHEN e.status = 'submitted' THEN e.rating END) AS average_rating,
    AVG(CASE WHEN e.status = 'submitted' THEN e.weighted_rating END) AS average_weighted_rating,
    MIN(CASE WHEN e.status = 'submitted' THEN e.rating END) AS min_rating,
    MAX(CASE WHEN e.status = 'submitted' THEN e.rating END) AS max_rating
FROM assignments a
JOIN cycles cy ON cy.id = a.cycle_id
JOIN people pt ON pt.email = a.target_email
LEFT JOIN evaluations e ON e.assignment_id = a.id
GROUP BY cy.code, a.target_email, pt.full_name
ORDER BY cycle_code, target_name;

-- ============================================================================
-- EOM REPORTING VIEWS
-- ============================================================================

-- 1) EOM: who can vote (list) and who are nominees (list)
-- Note: Uses NULL for optional columns that may not exist yet
CREATE OR REPLACE VIEW eom_participants AS
SELECT
    cy.code || '-EOM-' || LPAD(e.month::text, 2, '0') || '-' || e.year AS eom_code,
    'voter' AS kind,
    v.voter_email AS email,
    p.full_name,
    NULL::VARCHAR(100) AS role_title,  -- Will be populated once column exists
    NULL::staff_segment AS segment     -- Will be populated once column exists
FROM eom_voters v
JOIN eom_cycles e ON e.id = v.eom_cycle_id
JOIN cycles cy ON cy.id = e.cycle_id
LEFT JOIN people p ON p.email = v.voter_email
UNION ALL
SELECT
    cy.code || '-EOM-' || LPAD(e.month::text, 2, '0') || '-' || e.year AS eom_code,
    'nominee' AS kind,
    n.nominee_email AS email,
    p2.full_name,
    NULL::VARCHAR(100) AS role_title,  -- Will be populated once column exists
    NULL::staff_segment AS segment      -- Will be populated once column exists
FROM eom_nominees n
JOIN eom_cycles e ON e.id = n.eom_cycle_id
JOIN cycles cy ON cy.id = e.cycle_id
LEFT JOIN people p2 ON p2.email = n.nominee_email
ORDER BY eom_code, kind, full_name;

-- 2) EOM Nomination Summary
CREATE OR REPLACE VIEW eom_nomination_summary AS
SELECT
    cy.code || '-EOM-' || LPAD(e.month::text, 2, '0') || '-' || e.year AS eom_code,
    e.month,
    e.year,
    n.category,
    COUNT(DISTINCT n.nominee_email) AS nominee_count,
    COUNT(DISTINCT n.nominated_by) AS nominator_count,
    SUM(n.votes_received) AS total_votes,
    AVG(n.votes_received) AS avg_votes_per_nominee
FROM eom_nominees n
JOIN eom_cycles e ON e.id = n.eom_cycle_id
JOIN cycles cy ON cy.id = e.cycle_id
GROUP BY cy.code, e.month, e.year, n.category
ORDER BY e.year DESC, e.month DESC, n.category;

-- 3) EOM Winner History
CREATE OR REPLACE VIEW eom_winner_history AS
SELECT
    w.id,
    cy.code || '-EOM-' || LPAD(e.month::text, 2, '0') || '-' || e.year AS eom_code,
    w.winner_email,
    p.full_name AS winner_name,
    w.category,
    w.term,
    w.votes_received,
    w.announced_at,
    e.month,
    e.year
FROM eom_winners w
JOIN eom_cycles e ON e.id = w.eom_cycle_id
JOIN cycles cy ON cy.id = e.cycle_id
LEFT JOIN people p ON p.email = w.winner_email
ORDER BY e.year DESC, e.month DESC, w.announced_at DESC;

-- ============================================================================
-- SCORING VIEWS
-- ============================================================================

-- Weighted Score Summary by Staff Type
-- Note: Simplified to use only columns that exist, defaults to 'other' for staff_type
CREATE OR REPLACE VIEW weighted_score_summary AS
SELECT
    cy.code AS cycle_code,
    NULL::staff_segment AS segment,  -- Will be populated once column exists
    'other'::VARCHAR(20) AS staff_type,  -- Default, will be calculated once columns exist
    COUNT(DISTINCT a.target_email) AS staff_count,
    COUNT(e.id) AS total_evaluations,
    AVG(CASE WHEN e.status = 'submitted' THEN e.weighted_rating END) AS avg_weighted_score,
    AVG(CASE WHEN e.status = 'submitted' THEN e.rating END) AS avg_raw_score
FROM assignments a
JOIN cycles cy ON cy.id = a.cycle_id
JOIN people pt ON pt.email = a.target_email
LEFT JOIN evaluations e ON e.assignment_id = a.id
GROUP BY cy.code
ORDER BY cycle_code;

-- ============================================================================
-- AUDIT VIEWS
-- ============================================================================

-- Recent Audit Logs
CREATE OR REPLACE VIEW recent_audit_logs AS
SELECT
    al.id,
    al.action_type,
    al.entity_type,
    al.entity_id,
    al.user_email,
    p.full_name AS user_name,
    al.user_role,
    al.changes,
    al.timestamp
FROM audit_logs al
LEFT JOIN people p ON p.email = al.user_email
ORDER BY al.timestamp DESC
LIMIT 1000;


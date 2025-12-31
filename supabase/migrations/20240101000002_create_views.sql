-- Create Reporting Views for Eternity School Evaluation System

-- ============================================================================
-- MRE REPORTING VIEWS
-- ============================================================================

-- 1) MRE: Who evaluates who (names + roles)
-- Note: Uses COALESCE to handle missing role_title column gracefully
CREATE OR REPLACE VIEW mre_who_evaluates_who AS
SELECT
    cy.code          AS cycle_code,
    a.rater_email,
    pr.full_name     AS rater_name,
    COALESCE(a.rater_role, 
             CASE WHEN EXISTS (
                 SELECT 1 FROM information_schema.columns 
                 WHERE table_name = 'people' AND column_name = 'role_title'
             ) THEN pr.role_title ELSE NULL END
    ) AS rater_role,
    a.target_email,
    pt.full_name     AS target_name,
    COALESCE(a.target_role, 
             CASE WHEN EXISTS (
                 SELECT 1 FROM information_schema.columns 
                 WHERE table_name = 'people' AND column_name = 'role_title'
             ) THEN pt.role_title ELSE NULL END
    ) AS target_role,
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
CREATE OR REPLACE VIEW mre_evaluation_summary AS
SELECT
    cy.code AS cycle_code,
    a.target_email,
    pt.full_name AS target_name,
    pt.segment AS target_segment,
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
GROUP BY cy.code, a.target_email, pt.full_name, pt.segment
ORDER BY cycle_code, target_name;

-- ============================================================================
-- EOM REPORTING VIEWS
-- ============================================================================

-- 1) EOM: who can vote (list) and who are nominees (list)
-- Note: Uses NULLIF to handle missing role_title column
CREATE OR REPLACE VIEW eom_participants AS
SELECT
    cy.code || '-EOM-' || LPAD(e.month::text, 2, '0') || '-' || e.year AS eom_code,
    'voter' AS kind,
    v.voter_email AS email,
    p.full_name,
    CASE WHEN EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'people' AND column_name = 'role_title'
    ) THEN p.role_title ELSE NULL END AS role_title,
    CASE WHEN EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'people' AND column_name = 'segment'
    ) THEN p.segment ELSE NULL::staff_segment END AS segment
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
    CASE WHEN EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'people' AND column_name = 'role_title'
    ) THEN p2.role_title ELSE NULL END AS role_title,
    CASE WHEN EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'people' AND column_name = 'segment'
    ) THEN p2.segment ELSE NULL::staff_segment END AS segment
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
-- Note: Handles missing role_title and department columns
CREATE OR REPLACE VIEW weighted_score_summary AS
SELECT
    cy.code AS cycle_code,
    CASE WHEN EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'people' AND column_name = 'segment'
    ) THEN pt.segment ELSE NULL::staff_segment END AS segment,
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'people' AND column_name = 'role_title'
        ) AND (
            pt.role_title ILIKE '%teacher%' OR pt.role_title ILIKE '%instructor%' 
            OR pt.role_title ILIKE '%professor%'
        )
        THEN 'academic'
        WHEN EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'people' AND column_name = 'department'
        ) AND pt.department ILIKE '%academic%'
        THEN 'academic'
        WHEN EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'people' AND column_name = 'role_title'
        ) AND (
            pt.role_title ILIKE '%admin%' OR pt.role_title ILIKE '%coordinator%'
            OR pt.role_title ILIKE '%manager%'
        )
        THEN 'admin'
        WHEN EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'people' AND column_name = 'department'
        ) AND pt.department ILIKE '%admin%'
        THEN 'admin'
        ELSE 'other'
    END AS staff_type,
    COUNT(DISTINCT a.target_email) AS staff_count,
    COUNT(e.id) AS total_evaluations,
    AVG(CASE WHEN e.status = 'submitted' THEN e.weighted_rating END) AS avg_weighted_score,
    AVG(CASE WHEN e.status = 'submitted' THEN e.rating END) AS avg_raw_score
FROM assignments a
JOIN cycles cy ON cy.id = a.cycle_id
JOIN people pt ON pt.email = a.target_email
LEFT JOIN evaluations e ON e.assignment_id = a.id
WHERE CASE WHEN EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'people' AND column_name = 'active'
) THEN pt.active ELSE TRUE END = TRUE
GROUP BY cy.code, segment, staff_type
ORDER BY cycle_code, staff_type, segment;

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


-- ============================================================
-- Query A: Does Gen Chem grade tier (A/B vs C/D) predict
-- eventual Organic Chem success, allowing for gap semesters?
-- ============================================================
WITH gc_first_pass AS (
    SELECT anon_id, grade AS gc_grade, term_order AS gc_term
    FROM gen_chem_grades
    WHERE grade <> 'F'
      AND term_order = (
          SELECT MIN(term_order) FROM gen_chem_grades g2
          WHERE g2.anon_id = gen_chem_grades.anon_id AND g2.grade <> 'F'
      )
),
first_organic_attempt AS (
    SELECT anon_id, MIN(term_order) AS oc_term
    FROM org_chem_grades
    GROUP BY anon_id
),
progression AS (
    SELECT fp.anon_id,
           CASE WHEN fp.gc_grade IN ('C','C+','C-','D','D+','D-') THEN 'C/D' ELSE 'A/B' END AS gc_bucket,
           oc.grade AS oc_grade,
           foa.oc_term - fp.gc_term AS terms_gap
    FROM gc_first_pass fp
    LEFT JOIN first_organic_attempt foa ON foa.anon_id = fp.anon_id AND foa.oc_term > fp.gc_term
    LEFT JOIN org_chem_grades oc ON oc.anon_id = fp.anon_id AND oc.term_order = foa.oc_term
)
SELECT gc_bucket,
       COUNT(*) AS total_students,
       COUNT(oc_grade) AS eventually_took_organic,
       SUM(CASE WHEN oc_grade IN ('A','A-','B+','B','B-','C+','C','C-') THEN 1 ELSE 0 END) AS passed_organic,
       ROUND(100.0 * SUM(CASE WHEN oc_grade IN ('A','A-','B+','B','B-','C+','C','C-') THEN 1 ELSE 0 END)
             / NULLIF(COUNT(oc_grade),0), 1) AS pass_rate_pct,
       ROUND(AVG(terms_gap), 1) AS avg_terms_gap
FROM progression
GROUP BY gc_bucket;

-- ============================================================
-- Query B: Students who failed Gen Chem on the first attempt,
-- passed on retake -- did they go on to pass Organic Chem?
-- ============================================================
WITH gc_attempts AS (
    SELECT anon_id, grade, term_order,
           ROW_NUMBER() OVER (PARTITION BY anon_id ORDER BY term_order) AS attempt_num
    FROM gen_chem_grades
),
first_attempt_failed AS (
    SELECT anon_id FROM gc_attempts WHERE attempt_num = 1 AND grade = 'F'
),
retake_pass AS (
    SELECT a.anon_id, a.term_order AS retake_term, a.grade AS retake_grade
    FROM gc_attempts a
    JOIN first_attempt_failed f ON f.anon_id = a.anon_id
    WHERE a.attempt_num = 2 AND a.grade <> 'F'
),
first_organic_after_retake AS (
    SELECT rp.anon_id, MIN(oc.term_order) AS oc_term
    FROM retake_pass rp
    JOIN org_chem_grades oc ON oc.anon_id = rp.anon_id AND oc.term_order > rp.retake_term
    GROUP BY rp.anon_id
)
SELECT COUNT(DISTINCT rp.anon_id) AS retook_and_passed_genchem,
       COUNT(DISTINCT foa.anon_id) AS went_on_to_organic,
       SUM(CASE WHEN oc.grade IN ('A','A-','B+','B','B-','C+','C','C-') THEN 1 ELSE 0 END) AS passed_organic
FROM retake_pass rp
LEFT JOIN first_organic_after_retake foa ON foa.anon_id = rp.anon_id
LEFT JOIN org_chem_grades oc ON oc.anon_id = foa.anon_id AND oc.term_order = foa.oc_term;

-- ============================================================
-- Query C: Organic Chem pass rate by department and by class
-- standing at first Gen Chem attempt -- do later starters
-- (Junior/Senior, often transfers or major-switchers) perform
-- differently than students who start on the typical track?
-- ============================================================
WITH gc_first_pass AS (
    SELECT g.anon_id, g.grade AS gc_grade, g.term_order AS gc_term
    FROM gen_chem_grades g
    WHERE g.grade <> 'F'
      AND g.term_order = (
          SELECT MIN(term_order) FROM gen_chem_grades g2
          WHERE g2.anon_id = g.anon_id AND g2.grade <> 'F'
      )
),
first_organic_attempt AS (
    SELECT anon_id, MIN(term_order) AS oc_term
    FROM org_chem_grades
    GROUP BY anon_id
)
SELECT s.department,
       s.class_standing_gc,
       COUNT(*) AS students_in_group,
       COUNT(oc.grade) AS took_organic,
       SUM(CASE WHEN oc.grade IN ('A','A-','B+','B','B-','C+','C','C-') THEN 1 ELSE 0 END) AS passed_organic,
       ROUND(100.0 * SUM(CASE WHEN oc.grade IN ('A','A-','B+','B','B-','C+','C','C-') THEN 1 ELSE 0 END)
             / NULLIF(COUNT(oc.grade),0), 1) AS pass_rate_pct
FROM gc_first_pass fp
JOIN students s ON s.anon_id = fp.anon_id
LEFT JOIN first_organic_attempt foa ON foa.anon_id = fp.anon_id AND foa.oc_term > fp.gc_term
LEFT JOIN org_chem_grades oc ON oc.anon_id = fp.anon_id AND oc.term_order = foa.oc_term
GROUP BY s.department, s.class_standing_gc
ORDER BY s.department, s.class_standing_gc;


# Student Course Progression Analysis (SQL)

**SQL-based cohort analysis of prerequisite course performance and downstream success, using anonymized, hypothetical academic data.**

## Overview

This project models a common academic analytics question: *does performance in an introductory prerequisite course predict success in the follow-on course, and how much does gap time between courses matter?*

The dataset and scenario are **hypothetical and synthetically generated** they are modeled on the type of cohort-progression analysis commonly used by academic departments to evaluate prerequisite policy, but do not represent any real institution, real students, or real grades. All student identifiers are randomly generated anonymous codes (e.g. `STU-00042`); no names, IDs, or institutional data are used or included.

## Scenario

A chemistry department wants to know:
1. Do students who earn a C/D in General Chemistry succeed in Organic Chemistry at a meaningfully lower rate than A/B students?
2. How long is the typical gap between finishing General Chemistry and starting Organic Chemistry (course/lab availability doesn't guarantee the very next term)?
3. Among students who failed General Chemistry on their first attempt, retook it, and passed, how many went on to pass Organic Chemistry?

This kind of analysis directly informs real policy decisions, such as whether to raise the minimum prerequisite grade required to advance.

## Schema

```
terms              (term_order PK, term_label)
students           (anon_id PK, major, department, enrollment_type, class_standing_gc)
gen_chem_grades    (anon_id, term_order, grade)
org_chem_grades    (anon_id, term_order, grade)
```

Students are tracked only by `anon_id`, an unlinked, randomly assigned identifier — across both courses, any number of terms (including gap terms), and a `students` dimension table capturing major, department, enrollment type, and class standing at the time they first took General Chemistry. The dataset spans six majors across six departments (Chemistry, Biology, Pre-Health, Chemical Engineering, Nursing, Environmental Science), reflecting that General/Organic Chemistry are prerequisite service course for majors well beyond Chemistry itself.

## Key SQL Techniques Used

- **CTEs (`WITH`)** to break multi-step cohort logic into readable stages
- **Window functions** (`ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ...)`) to identify each student's first vs. retake attempts
- **Correlated subqueries** to find each student's first passing grade
- **LEFT JOINs on a non-fixed term offset** (`term_order > gc_term`, not `term_order = gc_term + 1`) to correctly handle students who skip a term before enrolling in the next course
- **CASE WHEN** for grade-tier bucketing (A/B vs. C/D) and pass/fail classification
- **Aggregate + ROUND** for pass-rate percentages and average term-gap reporting

## Results (on the synthetic dataset, N=1,200 students)

| Gen Chem Grade Tier | Students | Eventually Took Organic | Passed Organic | Pass Rate | Avg. Term Gap |
|---|---|---|---|---|---|
| A/B | 625 | 501 | 396 | **79.0%** | 1.5 terms |
| C/D | 574 | 243 | 129 | **53.1%** | 1.5 terms |

Students who failed General Chemistry on their first attempt, passed on retake, and later took Organic Chemistry: **143 retook and passed → 93 went on to Organic Chem → 63 passed**, illustrating that recovery is possible but success rates are still worth tracking separately from first-attempt A/B students.

These results are consistent with the kind of pattern that would support a prerequisite-policy conversation (e.g., requiring a B- or better in General Chemistry before enrolling in Organic Chemistry).

**Query C** breaks this down further by department and class standing at first Gen Chem attempt e.g. Chemistry majors who first took Gen Chem as Juniors (often transfers or major-switchers) passed Organic Chem at a notably higher rate (92.9%) than the typical Freshman-start cohort (67.4%), a pattern worth flagging to an advisor rather than assuming later starters are automatically higher-risk.

## Repository Structure

```
student-progression-sql/
├── generate_data.py           # Generates the synthetic, hypothetical dataset
├── data/
│   └── student_progression.db # SQLite database (generated)
├── sql/
│   └── analysis_queries.sql   # Full cohort progression analysis queries
└── README.md
```

## Run It

```bash
python3 generate_data.py
sqlite3 data/student_progression.db < sql/analysis_queries.sql
```

## Background

This project is modeled on a real type of analysis I supported informally, outside of teaching duties, while working with department-level student outcome data. This repository rebuilds that same analytical question, properly, in SQL, on synthetic data, as part of formalizing my SQL skills.

## Author

**Mahdi Aarabi, Ph.D.**
Computational Scientist

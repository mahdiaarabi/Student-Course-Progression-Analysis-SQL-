import sqlite3, random
random.seed(42)

conn = sqlite3.connect('data/student_progression.db')
cur = conn.cursor()

cur.executescript('''
DROP TABLE IF EXISTS terms;
DROP TABLE IF EXISTS students;
DROP TABLE IF EXISTS gen_chem_grades;
DROP TABLE IF EXISTS org_chem_grades;

CREATE TABLE terms (
    term_order INTEGER PRIMARY KEY,
    term_label TEXT NOT NULL
);

CREATE TABLE students (
    anon_id             TEXT PRIMARY KEY,
    major               TEXT NOT NULL,
    department          TEXT NOT NULL,
    enrollment_type     TEXT NOT NULL,   -- Full-time / Part-time
    class_standing_gc   TEXT NOT NULL    -- class standing when they FIRST took Gen Chem
);

CREATE TABLE gen_chem_grades (
    anon_id     TEXT NOT NULL,
    term_order  INTEGER NOT NULL,
    grade       TEXT NOT NULL,
    FOREIGN KEY (anon_id) REFERENCES students(anon_id),
    FOREIGN KEY (term_order) REFERENCES terms(term_order)
);

CREATE TABLE org_chem_grades (
    anon_id     TEXT NOT NULL,
    term_order  INTEGER NOT NULL,
    grade       TEXT NOT NULL,
    FOREIGN KEY (anon_id) REFERENCES students(anon_id),
    FOREIGN KEY (term_order) REFERENCES terms(term_order)
);
''')

terms = [(1,'Fall 2023'), (2,'Spring 2024'), (3,'Fall 2024'),
         (4,'Spring 2025'), (5,'Fall 2025'), (6,'Spring 2026')]
cur.executemany('INSERT INTO terms VALUES (?,?)', terms)

grades_pool = ['A','A-','B+','B','B-','C+','C','C-','D+','D','D-','F']
weights =     [ 8,  6,   9,  10,  9,   8,  9,  7,   5,  5,  4,  10]

# Majors grouped by department -- includes non-chemistry majors who still
# need Gen Chem/Organic Chem as a requirement (pre-health, biology, etc.)
majors_by_dept = {
    'Chemistry':          ['Chemistry', 'Biochemistry'],
    'Biology':             ['Biology', 'Molecular Biology'],
    'Pre-Health':          ['Pre-Pharmacy', 'Pre-Med (Biology)'],
    'Chemical Engineering':['Chemical Engineering'],
    'Nursing':             ['Nursing'],
    'Environmental Science':['Environmental Science'],
}
dept_weights = [22, 20, 18, 12, 20, 8]  # relative frequency

class_standings = ['Freshman', 'Sophomore', 'Junior', 'Senior']
# Most take Gen Chem as Freshman/Sophomore; a smaller tail (transfers,
# switched majors, prereq delays) take it later
standing_weights = [55, 28, 12, 5]

N_STUDENTS = 1200
students_rows = []
gen_chem_rows = []
org_chem_rows = []

for i in range(1, N_STUDENTS+1):
    anon_id = f"STU-{i:05d}"

    dept = random.choices(list(majors_by_dept.keys()), weights=dept_weights, k=1)[0]
    major = random.choice(majors_by_dept[dept])
    enrollment_type = random.choices(['Full-time','Part-time'], weights=[88,12], k=1)[0]
    class_standing_gc = random.choices(class_standings, weights=standing_weights, k=1)[0]

    # Students who start Gen Chem later (Junior/Senior) tend to start in a later term
    if class_standing_gc == 'Freshman':
        start_term = random.choices([1,2,3], weights=[70,20,10], k=1)[0]
    elif class_standing_gc == 'Sophomore':
        start_term = random.choices([1,2,3,4], weights=[10,40,30,20], k=1)[0]
    else:  # Junior/Senior -- later starters (transfers, switched majors)
        start_term = random.choices([2,3,4,5], weights=[10,30,35,25], k=1)[0]

    students_rows.append((anon_id, major, dept, enrollment_type, class_standing_gc))

    grade = random.choices(grades_pool, weights=weights, k=1)[0]
    gen_chem_rows.append((anon_id, start_term, grade))

    final_gc_grade = grade
    final_gc_term = start_term

    if grade == 'F' and start_term < 5:
        retake_term = start_term + 1
        retake_grade = random.choices(grades_pool[:-1], weights=weights[:-1], k=1)[0]
        gen_chem_rows.append((anon_id, retake_term, retake_grade))
        final_gc_grade = retake_grade
        final_gc_term = retake_term

    if final_gc_grade == 'F':
        continue

    is_cd = final_gc_grade in ['C','C+','C-','D','D+','D-']
    proceed_prob = 0.45 if is_cd else 0.85
    if random.random() > proceed_prob:
        continue

    gap = random.choices([1,2,3], weights=[6,3,1], k=1)[0]
    oc_term = final_gc_term + gap
    if oc_term > 6:
        continue

    if is_cd:
        oc_grade = random.choices(grades_pool, weights=[2,2,4,5,5,6,6,6,6,6,6,18], k=1)[0]
    else:
        oc_grade = random.choices(grades_pool, weights=[9,7,9,10,9,7,7,6,5,4,3,7], k=1)[0]

    org_chem_rows.append((anon_id, oc_term, oc_grade))

cur.executemany('INSERT INTO students VALUES (?,?,?,?,?)', students_rows)
cur.executemany('INSERT INTO gen_chem_grades VALUES (?,?,?)', gen_chem_rows)
cur.executemany('INSERT INTO org_chem_grades VALUES (?,?,?)', org_chem_rows)
conn.commit()

print(f"Students: {N_STUDENTS}")
print(f"Gen Chem grade records: {len(gen_chem_rows)}")
print(f"Org Chem grade records: {len(org_chem_rows)}")
conn.close()

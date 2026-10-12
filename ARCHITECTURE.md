# System Architecture & Optimization Specification
## "The Exam Timetable from Hell" — Intelligent Examination Timetable Generator

### 1. High-Level Architecture Overview

The system is engineered as an enterprise-grade, asynchronous university examination scheduling and resource optimization platform.

```
┌────────────────────────────────────────────────────────────────────────┐
│                   React 19 + TypeScript Frontend                       │
│  - Tailwind CSS Theme (Dark Navy / Slate with Indigo & Cyan Accents)   │
│  - Interactive Calendar Grid (Session, Room, Dept Views)               │
│  - Live Conflict Diagnostics Center                                    │
│  - Optimization Tuning Controls (S1-S8 Sliders & Mode Selection)       │
│  - Recharts Visualizations & Baseline Comparison Tables                │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │ REST APIs (JSON / Multipart)
┌────────────────────────────────────▼───────────────────────────────────┐
│                    FastAPI Backend Application                         │
│  - Pydantic v2 Schema Validation                                       │
│  - Asynchronous Background Job Manager (JobStore & Worker Threading)   │
│  - ReportLab PDF Engine & CSV Streaming Exporter                       │
│  - JWT Bearer Authentication & Audit Change Logging                    │
└──────────────┬──────────────────────────────────────────┬──────────────┘
               │                                          │
┌──────────────▼─────────────┐             ┌──────────────▼──────────────┐
│  SQLAlchemy ORM + Alembic  │             │    Optimization Core        │
│  - PostgreSQL 16 (Docker)  │             │    (Google OR-Tools CP-SAT) │
│  - SQLite Local Dev Mode   │             │  - Conflict Graph & Deg Ord │
│  - Timetable Versioning    │             │  - Exact Constraint Model   │
│  - Transactional Rollbacks │             │  - Independent Validator    │
└────────────────────────────┘             │  - Infeasibility Diagnostics│
                                           │  - Normalized Quality Engine│
                                           └─────────────────────────────┘
```

---

### 2. Constraint Programming Model (Google OR-Tools CP-SAT)

#### Decision Variables
- Let $E$ be the set of examinations.
- Let $S$ be the set of available, active time slots (excluding institutional blackouts).
- Let $R$ be the set of active rooms.
- Let $X_{e, s, r} \in \{0, 1\}$ represent whether examination $e$ is scheduled at time slot $s$ in room $r$.
- Let $Y_{e, s} = \sum_{r} X_{e, s, r}$ represent whether examination $e$ occurs at slot $s$.

#### Hard Constraints (Never Violated)
1. **H1. Student Conflict Prevention**:
   For any pair of examinations $(e_1, e_2)$ sharing at least one common student enrollment:
   $$\forall s \in S: \quad Y_{e_1, s} + Y_{e_2, s} \le 1$$
2. **H2. Room Usable Capacity**:
   Candidate filtering ensures $X_{e, s, r} = 0$ whenever $\text{Enrollment}(e) > \text{Capacity}(r)$.
3. **H3. Room Availability & Non-Overlap**:
   A room cannot host two examinations at the same time slot:
   $$\forall s \in S, \forall r \in R: \quad \sum_{e} X_{e, s, r} \le 1$$
   Rooms under scheduled maintenance blackouts are removed from candidate sets.
4. **H4. Examination Duration Respect**:
   Candidate filtering ensures $X_{e, s, r} = 0$ whenever $\text{Duration}(e) > \text{Duration}(s)$.
5. **H5. Time-Slot Availability & Blackouts**:
   Institutional holiday and blackout slots are strictly prohibited from hosting exams.
6. **H6. Locked Examination Preservation**:
   If an exam $e$ has been locked by an administrator to slot $s^*$ and room $r^*$:
   $$X_{e, s^*, r^*} = 1$$
7. **H7. Room Suitability & Equipment**:
   Candidate filtering verifies that $\text{RequiredFeatures}(e) \subseteq \text{RoomFeatures}(r)$.
8. **H8. Student Enrollment Eligibility**:
   Only students with verified course enrollments are counted and scheduled.
9. **H9. Assignment Completeness**:
   Every examination must be scheduled exactly once:
   $$\forall e \in E: \quad \sum_{(s, r) \in \text{Candidates}(e)} X_{e, s, r} = 1$$

---

### 3. Soft Constraints & Multi-Objective Cost Function

$$\text{Total Cost} = \sum_{i=1}^{8} w_i \cdot \text{Penalty}_i$$

- **S1 (Student Daily Burden)**: Penalizes assigning 2 or more exams to a student on the same date ($w_{\text{burden}} = 100$).
- **S2 (Exam Spacing & Rest)**: Penalizes assigning back-to-back adjacent sessions on the same date to students with shared courses ($w_{\text{spacing}} = 50$).
- **S3 & S8 (Daily Imbalance)**: Minimizes workload skew and standard deviation across exam dates ($w_{\text{imbalance}} = 30$).
- **S4 (Preferred Time Slots)**: Penalizes scheduling outside department-requested slots ($w_{\text{pref}} = 20$).
- **S5 (Seating Utilization Efficiency)**: Penalizes wasted seats in oversized venues ($w_{\text{util}} = 10$).
- **S6 (Minimal Disruption During Re-Optimization)**: Penalizes changing valid, unlocked assignments from the previous schedule version ($w_{\text{reassign}} = 150$).
- **S7 (Undesirable Sessions)**: Penalizes scheduling in evening sessions when morning/afternoon sessions are open ($w_{\text{undesirable}} = 40$).

---

### 4. Independent Validator & Infeasibility Diagnostics

The system strictly decouples the solver from the reporting layer:
1. **Independent Verification**: After the CP-SAT engine outputs assignments, the `TimetableValidator` independently audits all constraints H1 through H9 using pure database queries and set logic. A schedule is marked valid **only** if zero violations are detected.
2. **Root-Cause Infeasibility Diagnostics**:
   - `LOCKED_ROOM_DOUBLE_BOOKING`: Detects when two locked exams target the same venue and slot.
   - `LOCKED_STUDENT_CLASH`: Pinpoints shared students between locked exams on overlapping slots.
   - `DURATION_EXCEEDS_MAX_SLOT`: Identifies exams whose duration exceeds all active slots.
   - `NO_ROOM_WITH_ENOUGH_CAPACITY`: Highlights cohorts larger than the university's largest venue.
   - `CLIQUE_CONFLICT_SLOT_DEFICIT`: Computes the conflict graph chromatic lower bound against available slots.

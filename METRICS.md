# University Examination Timetable Quality Metrics Reference

### 1. Feasibility Metrics (Hard Constraints H1 — H9)

A timetable is mathematically feasible if and only if all feasibility metrics are exactly zero:

| Metric | Target | Formula / Definition | Consequence if > 0 |
|---|---|---|---|
| **Student Examination Clashes** | 0 | $\sum_{s \in S} \sum_{(u, v) \in \text{Edges}} (Y_{u, s} \cdot Y_{v, s})$ | Schedule strictly INVALID |
| **Room Double-Bookings** | 0 | $\sum_{s \in S, r \in R} \max(0, \sum_e X_{e, s, r} - 1)$ | Schedule strictly INVALID |
| **Room Capacity Overflows** | 0 | $\sum_{e, r} [ \text{Enrollment}(e) > \text{Capacity}(r) \text{ and } \text{Assigned}(e, r) ]$ | Schedule strictly INVALID |
| **Duration Truncations** | 0 | $\sum_{e, s} [ \text{Duration}(e) > \text{Duration}(s) \text{ and } \text{Assigned}(e, s) ]$ | Schedule strictly INVALID |
| **Blackout Violations** | 0 | Exams scheduled on holiday or maintenance dates | Schedule strictly INVALID |
| **Unscheduled Examinations** | 0 | Total exams minus completed valid assignments | Timetable INCOMPLETE |

---

### 2. Quality Metrics (Soft Constraints S1 — S8)

#### A. Student Daily Burden (% Multiple Same Day)
- **Definition**: Percentage of enrolled students who have more than one examination scheduled on a single calendar day.
- **Formula**:
  $$\text{PctMultipleSameDay} = \frac{\text{Count}(\{ u \in \text{Students} \mid \exists d: \text{ExamsTaken}(u, d) > 1 \})}{\text{TotalStudents}} \times 100\%$$
- **Ideal Value**: $< 5\%$ in multi-day scheduling periods.

#### B. Back-to-Back Rest Violations
- **Definition**: Count of instances where a student has two examinations scheduled in consecutive sessions (e.g. Morning then Afternoon) on the same day.
- **Ideal Value**: $0$ instances.

#### C. Average Examination Gap
- **Definition**: The average number of calendar days between consecutive examinations for a student taking multiple courses.
- **Formula**:
  $$\text{AvgGapDays} = \frac{1}{\sum (K_u - 1)} \sum_{u} \sum_{i=1}^{K_u - 1} (\text{Date}_{i+1} - \text{Date}_i)$$

#### D. Room Seating Utilization Rate
- **Definition**: Total student seats allocated divided by total capacity of all utilized examination rooms.
- **Formula**:
  $$\text{RoomUtilizationPct} = \frac{\sum_{a} \text{AssignedStudentCount}(a)}{\sum_{a} \text{RoomCapacity}(a)} \times 100\%$$
- **Target**: $60\% - 85\%$ (prevents venue waste while allowing adequate spacing).

#### E. Daily Load Imbalance (Standard Deviation)
- **Definition**: Standard deviation of the count of examinations scheduled across examination dates.
- **Formula**:
  $$\sigma_{\text{daily}} = \sqrt{\frac{1}{D} \sum_{d=1}^{D} (N_d - \bar{N})^2}$$

---

### 3. Normalized Quality Score (0 to 100)

The timetable quality score provides an interpretable measure of soft-constraint optimality:

$$\text{Quality Score} = 100.0 - \Delta_{\text{unscheduled}} - \Delta_{\text{burden}} - \Delta_{\text{b2b}} - \Delta_{\text{imbalance}} - \Delta_{\text{pref}} - \Delta_{\text{waste}} - \Delta_{\text{undesirable}}$$

- **Base Score**: 100.0 points.
- **Hard Constraint Fallback**: If independent validation identifies any hard constraint violation, the score is forced to **0.0** and prominently badged as **INVALID SCHEDULE**.
- **Deductions**:
  - Unscheduled Exams: Deducts up to 100 points ($100 \times \frac{\text{Unscheduled}}{\text{Total}}$).
  - Student Burden ($25$ max points): Deducted proportionally to % students with same-day multiple exams.
  - Back-to-Back ($20$ max points): Deducted based on rest interval breaches.
  - Daily Imbalance ($15$ max points): Deducted based on daily standard deviation ($3 \times \sigma_{\text{daily}}$).
  - Preferences ($15$ max points): Deducted for non-preferred slot deviations.
  - Room Efficiency ($15$ max points): Deducted when room utilization is below $60\%$.
  - Undesirable Sessions ($10$ max points): Deducted for evening session placements.

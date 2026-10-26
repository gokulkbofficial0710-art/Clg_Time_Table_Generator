# The Exam Timetable from Hell — Intelligent Examination Timetable Generator

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Google OR-Tools](https://img.shields.io/badge/Google_OR--Tools-CP--SAT-4285F4?logo=google&logoColor=white)](https://developers.google.com/optimization)
[![React 19](https://img.shields.io/badge/React-19.2-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.x-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-4.x-38B2AC?logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![Pytest](https://img.shields.io/badge/Tests-Pytest%20+%20Vitest-brightgreen)](https://docs.pytest.org)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/gokulkbofficial0710-art/Clg_Time_Table_Generator)
[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/template/new?template=https://github.com/gokulkbofficial0710-art/Clg_Time_Table_Generator)

An enterprise-grade, constraint-based university examination scheduling system powered by **Google OR-Tools CP-SAT**. Automatically generates clash-free exam timetables while honoring student cohorts, venue capacities, room feature suitability, exam durations, administrative locks, and weighted soft constraints.

---

## 1. System Architecture & Features

### Core Capabilities
- **Exact Constraint Optimization**: Formulated on Google OR-Tools CP-SAT (`cp_model.CpModel`) enforcing Hard Constraints H1 through H9.
- **Independent Validation Pipeline**: Pure algorithmic secondary auditor that inspects all assignments independently of the solver.
- **Root-Cause Diagnostics**: Deep analysis engine identifying locked clashes, room capacity bottlenecks, duration discrepancies, and conflict graph clique slot lower bounds.
- **Re-Optimization & Preservation**: Supports both **Full Optimization** and **Minimal-Change Optimization** to preserve existing valid schedules while strictly honoring locked exams.
- **Multi-Objective Soft Penalties (S1 — S8)**: Configurable weights for student daily burden, back-to-back exam spacing, daily workload balance, venue utilization, and department preferences.
- **Interactive University Admin Interface**: Modern Dark Navy / Slate theme featuring session calendar grids, room views, department views, student personal schedules, conflict centers, and version restore.
- **Auditable Exports**: Full PDF export powered by ReportLab with printable layout, plus CSV tabular export.

---

## 2. Technology Stack

- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS v4, Lucide React, React Router v7, TanStack Query, Recharts.
- **Backend**: Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy ORM, Alembic migrations, ReportLab.
- **Optimization**: Google OR-Tools CP-SAT Constraint Programming Solver.
- **Database**: PostgreSQL 16 (production/Docker) & SQLite (zero-dependency local development fallback).
- **Testing**: Pytest (backend & algorithms), Vitest & React Testing Library (frontend), Playwright (E2E).

---

## 3. Quick Start & Execution

### Prerequisites
- Python 3.10+ (Python 3.12 or 3.13 supported)
- Node.js 18+ & npm

### Method 1: One-Click Launch (Recommended for all machines)

- **On Windows**: Double-click `start.bat` (or run `.\start.ps1` in PowerShell).
- **On Linux / macOS**: Run `./start.sh` in terminal.

The launcher automatically checks the environment, runs migrations, verifies the build, and starts the server.

---

### Method 2: Manual Step-by-Step Setup

#### A. Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create & activate virtual environment (optional but recommended)
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start FastAPI backend (port 8000)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### B. Frontend Setup
```bash
# Open a new terminal in the frontend directory
cd frontend

# Install npm dependencies
npm install

# Option 1: Start Vite development server (port 5173 with hot reload)
npm run dev

# Option 2: Build for production (served directly by backend on port 8000)
npm run build
```

#### Accessing the Application:
- **Unified Production Server**: `http://localhost:8000` (FastAPI serves both UI and API together)
- **Development Server**: `http://localhost:5173` (Vite dev server)
- **API Documentation**: `http://localhost:8000/docs`
- **Network / Other Machines on LAN**: `http://<HOST_IP_ADDRESS>:8000` or `http://<HOST_IP_ADDRESS>:5173`

---

## 4. Docker Compose Setup (Optional)

To start PostgreSQL, backend, and frontend via Docker Compose:

```bash
docker compose up --build
```

- Web UI: `http://localhost:5173`
- API Docs: `http://localhost:8000/docs`
- PostgreSQL Port: `5432`

---

## 5. Automated Test Suite

### Running Backend & Scheduling Engine Tests
```bash
cd backend
python -m pytest -v
```

**Test Coverage**:
- Hard constraints H1 - H9 unit tests (`test_scheduling_engine.py`)
- Independent validator & diagnostics (`test_validator_and_diagnostics.py`)
- Edge cases: 0 exams, 0 rooms, excessive durations (`test_edge_cases.py`)
- REST API endpoints (`test_api.py`)
- Complete 12-step End-to-End lifecycle workflow (`test_e2e_workflow.py`)

### Running Frontend Tests
```bash
cd frontend
npm test
```

---

## 6. Demonstration Workflow

The application includes a deterministic benchmark dataset loaded automatically on first launch:
1. **Explore the Dashboard**: View total examinations (22), student cohort (60), available rooms (6), and initial baseline score.
2. **Review Initial Baseline Clashes**: Note the baseline schedule deliberately contains 1 student clash and 1 venue overflow.
3. **Execute CP-SAT Solver**:
   - Navigate to **Optimization Engine**.
   - Choose **Full Optimization** mode with default 30s time limit.
   - Click **Execute Timetable Solver**.
   - Observe solver status: `FEASIBLE` / `OPTIMAL` with runtime in milliseconds.
   - The quality score jumps to **90+ / 100** with **0 Hard Constraint Clashes**.
4. **Inspect Interactive Calendar**:
   - Navigate to **Timetable Grid**.
   - Switch between **Session Grid**, **Room View**, and **Department View**.
   - Filter by course code or venue.
5. **Lock an Examination**:
   - In **Examinations** or on the calendar, click the Lock icon on `EXAM-CS499` (Senior Capstone).
   - The lock status synchronizes with the database.
6. **Perform Minimal-Change Re-Optimization**:
   - Navigate to **Optimization Engine**.
   - Select **Minimal Change** mode.
   - Click **Execute Timetable Solver**.
   - The locked examination remains at its exact assigned coordinates while unlocked assignments are minimally disturbed.
7. **Inject Infeasible Scenario to Verify Diagnostics**:
   - On the **Dashboard** or **Data & Versions** page, click **Load Infeasible Demo**.
   - Navigate to **Conflict Center**.
   - The diagnostics engine immediately flags the impossibility:
     `"Scheduling conflict: 'EXAM-CS101' and 'EXAM-MA101' share 15 student(s), but both are locked to overlapping time slot 'SLOT-D1-M'."`
   - Notice that the quality score automatically drops to 0.0 and marks the schedule as **INVALID SCHEDULE**.
8. **Export Timetable**:
   - Click **Export PDF** or navigate to **Data & Versions** to generate a landscape printable PDF report via ReportLab or download the full CSV spreadsheet.

---

## 7. How to Interpret Solver Statuses & Quality Metrics

### Solver Outcomes
- **OPTIMAL**: A solution proven to be mathematically optimal for the weighted objective.
- **FEASIBLE**: A provably clash-free timetable satisfies all hard constraints H1 - H9.
- **INFEASIBLE**: Constraints are mathematically contradictory (e.g. conflicting locked exams, insufficient rooms, or duration mismatches). The diagnostics engine pinpoints the root cause.
- **UNKNOWN**: Time limit reached before finding a feasible incumbent.

### Quality Score (0 to 100)
A normalized score quantifying soft-constraint efficiency:
- **100.0**: Perfectly distributed timetable with zero same-day multiple exams, generous spacing, optimal room utilization, and full preference satisfaction.
- **80.0 — 95.0**: High-quality university timetable with minor trade-offs.
- **0.0 / INVALID**: Triggered whenever any hard constraint is breached. Hard violations are never masked by high soft scores.

---

## 8. REST API Endpoints Overview

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Service health status |
| `GET` | `/api/analytics/dashboard` | Real-time KPIs, clash counts, active schedule score |
| `GET` | `/api/analytics/distributions` | Exam date, room utilization, and student burden charts |
| `GET` | `/api/timetable` | Active timetable assignments (filterable) |
| `POST` | `/api/timetable/generate` | Run OR-Tools CP-SAT optimizer |
| `POST` | `/api/timetable/reoptimize` | Run minimal-change re-optimization |
| `POST` | `/api/timetable/validate` | Independent validator execution |
| `PATCH` | `/api/timetable/assignments/{id}` | Manual slot/room assignment with validation check |
| `PATCH` | `/api/timetable/assignments/{id}/lock` | Lock/unlock assignment toggle |
| `GET` | `/api/timetable/versions` | List version history with metrics |
| `POST` | `/api/timetable/restore/{version_id}` | Restore a historical timetable version |
| `GET` | `/api/timetable/compare` | Baseline versus candidate schedule comparison |
| `GET` | `/api/conflicts` | Diagnostics engine infeasibility and violation feed |
| `POST` | `/api/data/load-demo` | Reset to clean deterministic university dataset |
| `POST` | `/api/data/load-infeasible` | Configure intentional clash scenario |
| `GET` | `/api/export/timetable/csv` | Tabular CSV timetable export |
| `GET` | `/api/export/timetable/pdf` | ReportLab landscape PDF timetable export |

---

## 9. License

Developed for Academic and University Examination Scheduling Administration.

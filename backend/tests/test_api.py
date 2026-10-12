import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal, Base, engine
from app.services.demo_data import load_demo_dataset

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    load_demo_dataset(db)
    db.close()

def test_health_check_api():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"

def test_dashboard_api():
    response = client.get("/api/analytics/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert data["total_exams"] >= 20
    assert data["total_students"] >= 50
    assert "quality_score" in data

def test_get_exams_api():
    response = client.get("/api/exams")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 20
    assert any(e["exam_code"] == "EXAM-CS101" for e in data)

def test_get_rooms_api():
    response = client.get("/api/rooms")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 5

def test_get_timeslots_api():
    response = client.get("/api/time-slots")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 8

def test_get_timetable_api():
    # In baseline reset state, timetable grid is empty
    response = client.get("/api/timetable")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0

    # After optimization extraction, timetable grid is populated
    gen_res = client.post("/api/timetable/generate", json={"time_limit_seconds": 5})
    assert gen_res.status_code == 200
    response2 = client.get("/api/timetable")
    assert response2.status_code == 200
    data2 = response2.json()
    assert len(data2) >= 20

def test_validate_endpoint():
    response = client.post("/api/timetable/validate")
    assert response.status_code == 200
    data = response.json()
    assert "is_feasible" in data
    assert "violations" in data

def test_conflicts_endpoint():
    response = client.get("/api/conflicts")
    assert response.status_code == 200
    data = response.json()
    assert "total_conflicts" in data

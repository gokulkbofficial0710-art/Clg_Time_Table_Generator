from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.core.security import get_password_hash
from app.models.user import User
from app.models.room import Room
from app.services.demo_data import load_demo_dataset

# API Routers
from app.api.auth import router as auth_router
from app.api.exams import router as exams_router
from app.api.students import router as students_router
from app.api.rooms import router as rooms_router
from app.api.timeslots import router as timeslots_router
from app.api.timetable import router as timetable_router
from app.api.conflicts import router as conflicts_router
from app.api.analytics import router as analytics_router
from app.api.data_io import router as data_io_router
from app.api.backlogs import router as backlogs_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables
    Base.metadata.create_all(bind=engine)

    # Seed default admin user and demo dataset if database is fresh
    db = SessionLocal()
    try:
        default_users = [
            ("admin", "admin@university.edu", "admin123", "University Administrator", "admin"),
            ("faculty", "faculty@university.edu", "faculty123", "Faculty / Department Head", "editor"),
            ("coe", "coe@university.edu", "coe123", "Controller of Examinations", "admin"),
            ("student", "student@university.edu", "student123", "Student Portal Viewer", "viewer"),
        ]
        for uname, uemail, upass, ufullname, urole in default_users:
            if not db.query(User).filter_by(username=uname).first():
                user_obj = User(
                    username=uname,
                    email=uemail,
                    hashed_password=get_password_hash(upass),
                    full_name=ufullname,
                    role=urole,
                    is_active=True
                )
                db.add(user_obj)
        db.commit()

        # Check if rooms table is empty, auto-load demo data so user gets immediate out-of-the-box working experience
        if db.query(Room).count() == 0:
            load_demo_dataset(db)
    finally:
        db.close()

    yield

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Intelligent Examination Timetable Generator powered by Google OR-Tools CP-SAT",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health Check
@app.get("/api/health")
def health_check():
    return {
        "status": "HEALTHY",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }

# Register API Routers
app.include_router(auth_router, prefix="/api")
app.include_router(exams_router, prefix="/api")
app.include_router(students_router, prefix="/api")
app.include_router(rooms_router, prefix="/api")
app.include_router(timeslots_router, prefix="/api")
app.include_router(timetable_router, prefix="/api")
app.include_router(conflicts_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(data_io_router, prefix="/api")
app.include_router(backlogs_router, prefix="/api")

# Static frontend hosting for unified, zero-configuration deployment
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse

frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist.is_dir():
    assets_dir = frontend_dist / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/")
    async def serve_root():
        return FileResponse(frontend_dist / "index.html")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith(("api/", "docs", "redoc", "openapi.json")):
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Not Found")
        file_path = frontend_dist / full_path
        if full_path and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(frontend_dist / "index.html")


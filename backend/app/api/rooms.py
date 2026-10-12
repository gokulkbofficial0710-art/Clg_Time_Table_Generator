from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.room import Room
from app.models.timetable import TimetableVersion
from app.models.assignment import TimetableAssignment
from app.schemas.room import RoomCreate, RoomUpdate, RoomResponse
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/rooms", tags=["Rooms"])

@router.get("", response_model=List[RoomResponse])
def get_all_rooms(db: Session = Depends(get_db)):
    rooms = db.query(Room).order_by(Room.id).all()
    return rooms

@router.get("/{id}", response_model=RoomResponse)
def get_room_by_id(id: int, db: Session = Depends(get_db)):
    r = db.query(Room).filter_by(id=id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Room not found")
    return r

@router.post("", response_model=RoomResponse)
def create_room(req: RoomCreate, db: Session = Depends(get_db)):
    existing = db.query(Room).filter_by(room_code=req.room_code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Room with code '{req.room_code}' already exists")
    room = Room(
        room_code=req.room_code,
        name=req.name,
        building=req.building,
        capacity=req.capacity,
        is_available=req.is_available,
        features=req.features,
        accessibility_features=req.accessibility_features,
        blackout_intervals=req.blackout_intervals
    )
    db.add(room)
    db.commit()
    db.refresh(room)
    return room

@router.put("/{id}", response_model=RoomResponse)
def update_room(id: int, req: RoomUpdate, db: Session = Depends(get_db)):
    room = db.query(Room).filter_by(id=id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    if req.room_code and req.room_code != room.room_code:
        conflict = db.query(Room).filter_by(room_code=req.room_code).first()
        if conflict:
            raise HTTPException(status_code=400, detail=f"Room code '{req.room_code}' already taken")
        room.room_code = req.room_code

    if req.name is not None:
        room.name = req.name
    if req.building is not None:
        room.building = req.building
    if req.capacity is not None:
        room.capacity = req.capacity
    if req.is_available is not None:
        room.is_available = req.is_available
    if req.features is not None:
        room.features = req.features
    if req.accessibility_features is not None:
        room.accessibility_features = req.accessibility_features
    if req.blackout_intervals is not None:
        room.blackout_intervals = req.blackout_intervals

    db.commit()
    db.refresh(room)
    return room

@router.delete("/{id}", response_model=MessageResponse)
def delete_room(id: int, db: Session = Depends(get_db)):
    room = db.query(Room).filter_by(id=id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    name = room.name
    db.delete(room)
    db.commit()
    return MessageResponse(message=f"Room '{name}' deleted successfully.")

@router.get("/{id}/occupancy")
def get_room_occupancy(id: int, db: Session = Depends(get_db)):
    room = db.query(Room).filter_by(id=id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    active_ver = db.query(TimetableVersion).filter_by(is_active=True).first()
    if not active_ver:
        return {"room_code": room.room_code, "capacity": room.capacity, "bookings": []}

    assignments = (
        db.query(TimetableAssignment)
        .filter(
            TimetableAssignment.timetable_id == active_ver.id,
            TimetableAssignment.room_id == room.id
        )
        .all()
    )

    bookings = []
    for a in assignments:
        if a.timeslot:
            bookings.append({
                "assignment_id": a.id,
                "exam_code": a.exam.exam_code,
                "course_name": a.exam.course_name,
                "date": str(a.timeslot.date),
                "start_time": str(a.timeslot.start_time),
                "end_time": str(a.timeslot.end_time),
                "period": a.timeslot.period,
                "assigned_students": a.assigned_student_count,
                "capacity": room.capacity,
                "occupancy_rate": round((a.assigned_student_count / room.capacity) * 100, 1),
                "is_locked": a.is_locked
            })
    return {"room_code": room.room_code, "capacity": room.capacity, "bookings": bookings}

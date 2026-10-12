from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.timeslot import TimeSlot
from app.schemas.timeslot import TimeSlotCreate, TimeSlotUpdate, TimeSlotResponse
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/time-slots", tags=["Time Slots"])

@router.get("", response_model=List[TimeSlotResponse])
def get_all_time_slots(db: Session = Depends(get_db)):
    slots = db.query(TimeSlot).order_by(TimeSlot.date, TimeSlot.start_time).all()
    return slots

@router.get("/{id}", response_model=TimeSlotResponse)
def get_time_slot_by_id(id: int, db: Session = Depends(get_db)):
    slot = db.query(TimeSlot).filter_by(id=id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Time slot not found")
    return slot

@router.post("", response_model=TimeSlotResponse)
def create_time_slot(req: TimeSlotCreate, db: Session = Depends(get_db)):
    existing = db.query(TimeSlot).filter_by(slot_code=req.slot_code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Slot with code '{req.slot_code}' already exists")
    slot = TimeSlot(
        slot_code=req.slot_code,
        date=req.date,
        start_time=req.start_time,
        end_time=req.end_time,
        duration_minutes=req.duration_minutes,
        period=req.period,
        is_available=req.is_available,
        is_blackout=req.is_blackout,
        blackout_reason=req.blackout_reason
    )
    db.add(slot)
    db.commit()
    db.refresh(slot)
    return slot

@router.put("/{id}", response_model=TimeSlotResponse)
def update_time_slot(id: int, req: TimeSlotUpdate, db: Session = Depends(get_db)):
    slot = db.query(TimeSlot).filter_by(id=id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Time slot not found")

    if req.slot_code and req.slot_code != slot.slot_code:
        conflict = db.query(TimeSlot).filter_by(slot_code=req.slot_code).first()
        if conflict:
            raise HTTPException(status_code=400, detail=f"Slot code '{req.slot_code}' already taken")
        slot.slot_code = req.slot_code

    if req.date is not None:
        slot.date = req.date
    if req.start_time is not None:
        slot.start_time = req.start_time
    if req.end_time is not None:
        slot.end_time = req.end_time
    if req.duration_minutes is not None:
        slot.duration_minutes = req.duration_minutes
    if req.period is not None:
        slot.period = req.period
    if req.is_available is not None:
        slot.is_available = req.is_available
    if req.is_blackout is not None:
        slot.is_blackout = req.is_blackout
    if req.blackout_reason is not None:
        slot.blackout_reason = req.blackout_reason

    db.commit()
    db.refresh(slot)
    return slot

@router.delete("/{id}", response_model=MessageResponse)
def delete_time_slot(id: int, db: Session = Depends(get_db)):
    slot = db.query(TimeSlot).filter_by(id=id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Time slot not found")
    code = slot.slot_code
    db.delete(slot)
    db.commit()
    return MessageResponse(message=f"Time slot '{code}' deleted successfully.")

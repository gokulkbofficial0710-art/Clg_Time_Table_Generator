from typing import Optional
from datetime import date, time
from pydantic import BaseModel, Field, ConfigDict

class TimeSlotBase(BaseModel):
    slot_code: str = Field(..., description="Unique slot identifier, e.g. SLOT-01")
    date: date
    start_time: time
    end_time: time
    duration_minutes: int = Field(..., ge=15, description="Slot duration in minutes")
    period: str = Field("Morning", description="Morning, Afternoon, or Evening")
    is_available: bool = True
    is_blackout: bool = False
    blackout_reason: Optional[str] = None

class TimeSlotCreate(TimeSlotBase):
    pass

class TimeSlotUpdate(BaseModel):
    slot_code: Optional[str] = None
    date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    duration_minutes: Optional[int] = Field(None, ge=15)
    period: Optional[str] = None
    is_available: Optional[bool] = None
    is_blackout: Optional[bool] = None
    blackout_reason: Optional[str] = None

class TimeSlotResponse(TimeSlotBase):
    model_config = ConfigDict(from_attributes=True)
    id: int

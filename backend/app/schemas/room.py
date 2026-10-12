from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class RoomBase(BaseModel):
    room_code: str = Field(..., description="Unique room identifier, e.g. HALL-A")
    name: str = Field(..., description="Human readable name, e.g. Main Auditorium")
    building: str = Field(..., description="Building name or number")
    capacity: int = Field(..., ge=1, description="Seating capacity for examinations")
    is_available: bool = True
    features: List[str] = Field(default_factory=list, description="Available features e.g. Computers, Projector")
    accessibility_features: List[str] = Field(default_factory=list)
    blackout_intervals: List[Dict[str, Any]] = Field(default_factory=list)

class RoomCreate(RoomBase):
    pass

class RoomUpdate(BaseModel):
    room_code: Optional[str] = None
    name: Optional[str] = None
    building: Optional[str] = None
    capacity: Optional[int] = Field(None, ge=1)
    is_available: Optional[bool] = None
    features: Optional[List[str]] = None
    accessibility_features: Optional[List[str]] = None
    blackout_intervals: Optional[List[Dict[str, Any]]] = None

class RoomResponse(RoomBase):
    model_config = ConfigDict(from_attributes=True)
    id: int

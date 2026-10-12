from typing import Generic, TypeVar, List, Optional, Any
from pydantic import BaseModel

T = TypeVar("T")

class MessageResponse(BaseModel):
    message: str
    success: bool = True
    details: Optional[Any] = None

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int

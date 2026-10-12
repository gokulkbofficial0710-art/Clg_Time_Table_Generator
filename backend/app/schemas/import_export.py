from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class ImportPreviewItem(BaseModel):
    row_number: int
    data: Dict[str, Any]
    status: str # VALID, INVALID, WARNING
    errors: List[str] = []

class ImportPreviewResponse(BaseModel):
    entity_type: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    preview_items: List[ImportPreviewItem]
    can_commit: bool

class ImportCommitRequest(BaseModel):
    entity_type: str
    items: List[Dict[str, Any]]
    overwrite_existing: bool = False

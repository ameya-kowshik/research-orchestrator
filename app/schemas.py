from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime

# --- Request ---
class ResearchRequest(BaseModel):
    query: str

# --- Response ---
class ReportResponse(BaseModel):
    id: str
    query: str
    report_type: Optional[str]
    title: Optional[str]
    sections: Optional[Dict[str, str]]
    key_points: Optional[List[str]]
    search_count: int
    created_at: datetime

    class Config:
        from_attributes = True

class ReportListResponse(BaseModel):
    reports: List[ReportResponse]
    total: int

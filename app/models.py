from sqlalchemy import Column, String, Integer, JSON, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base
import uuid

class ResearchReport(Base):
    __tablename__ = "research_reports"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    query = Column(Text, nullable=False)
    report_type = Column(String, nullable=True)
    title = Column(String, nullable=True)
    sections = Column(JSON, nullable=True)       # Dict[str, str]
    key_points = Column(JSON, nullable=True)     # List[str]
    search_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

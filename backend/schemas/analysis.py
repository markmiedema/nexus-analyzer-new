"""
Analysis schemas for request/response validation.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import date, datetime
from uuid import UUID
from models.analysis import AnalysisStatus


class AnalysisBase(BaseModel):
    """Base analysis schema with common fields."""
    client_name: str = Field(..., min_length=1, max_length=255, description="Client company name")
    period_start: date = Field(..., description="Start date of analysis period")
    period_end: date = Field(..., description="End date of analysis period")


class AnalysisCreate(AnalysisBase):
    """
    Schema for creating a new analysis.
    Frontend sends client_name and date range.
    """
    pass


class AnalysisUpdate(BaseModel):
    """Schema for updating an analysis."""
    client_name: Optional[str] = Field(None, min_length=1, max_length=255)
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    status: Optional[AnalysisStatus] = None
    error_message: Optional[str] = None


class AnalysisResponse(AnalysisBase):
    """
    Schema for analysis responses.
    Matches what frontend expects in api.ts.
    """
    analysis_id: UUID
    tenant_id: UUID
    created_by: Optional[UUID] = None
    status: AnalysisStatus
    analysis_date: date
    csv_file_path: Optional[str] = None
    validation_report_path: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AnalysisListResponse(BaseModel):
    """Schema for listing analyses with pagination."""
    items: list[AnalysisResponse]
    total: int
    page: int = 1
    page_size: int = 50

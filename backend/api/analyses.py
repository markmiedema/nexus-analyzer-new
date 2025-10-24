"""
Analyses API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from datetime import datetime

from database import get_db
from models.user import User
from models.analysis import Analysis, AnalysisStatus
from dependencies.auth import get_current_user
from schemas.analysis import (
    AnalysisCreate,
    AnalysisUpdate,
    AnalysisResponse,
    AnalysisListResponse
)
from services.csv_processor import csv_processor
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED)
async def create_analysis(
    analysis_data: AnalysisCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new analysis.

    This is the first step in the analysis workflow:
    1. Create analysis (this endpoint)
    2. Upload CSV file
    3. Process data
    4. Generate results

    - **client_name**: Name of the client company
    - **period_start**: Start date for analysis period
    - **period_end**: End date for analysis period
    """

    # Validate date range
    if analysis_data.period_start > analysis_data.period_end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Period start date must be before end date"
        )

    # Create new analysis
    analysis = Analysis(
        tenant_id=current_user.tenant_id,
        created_by=current_user.user_id,
        client_name=analysis_data.client_name,
        period_start=analysis_data.period_start,
        period_end=analysis_data.period_end,
        status=AnalysisStatus.PENDING
    )

    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    return analysis


@router.get("", response_model=List[AnalysisResponse])
async def list_analyses(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all analyses for the current user's tenant.

    Results are ordered by creation date (newest first).

    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return
    """

    analyses = db.query(Analysis).filter(
        Analysis.tenant_id == current_user.tenant_id
    ).order_by(
        Analysis.created_at.desc()
    ).offset(skip).limit(limit).all()

    return analyses


@router.get("/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(
    analysis_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific analysis by ID.

    Returns complete analysis details including status, dates, and file paths.
    """

    analysis = db.query(Analysis).filter(
        Analysis.analysis_id == analysis_id,
        Analysis.tenant_id == current_user.tenant_id
    ).first()

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )

    return analysis


@router.put("/{analysis_id}", response_model=AnalysisResponse)
async def update_analysis(
    analysis_id: UUID,
    analysis_data: AnalysisUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing analysis.

    Only pending or failed analyses can be updated.
    """

    analysis = db.query(Analysis).filter(
        Analysis.analysis_id == analysis_id,
        Analysis.tenant_id == current_user.tenant_id
    ).first()

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )

    # Check if analysis can be updated
    if analysis.status not in [AnalysisStatus.PENDING, AnalysisStatus.FAILED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot update analysis in {analysis.status} status"
        )

    # Update fields
    update_data = analysis_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(analysis, field, value)

    db.commit()
    db.refresh(analysis)

    return analysis


@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_analysis(
    analysis_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete an analysis.

    This will cascade delete all related data (business profile, transactions,
    nexus results, liability estimates, reports).
    """

    analysis = db.query(Analysis).filter(
        Analysis.analysis_id == analysis_id,
        Analysis.tenant_id == current_user.tenant_id
    ).first()

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )

    db.delete(analysis)
    db.commit()

    return None


@router.post("/{analysis_id}/upload")
@limiter.limit("10/hour")
async def upload_csv_to_analysis(
    request: Request,
    analysis_id: UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload CSV file to an existing analysis.

    This endpoint:
    1. Validates the analysis exists and is in PENDING status
    2. Uploads the file to S3/MinIO
    3. Triggers background CSV processing task
    4. Returns updated analysis with PENDING status

    Rate limited to 10 uploads per hour per user.

    - **file**: CSV file with transaction data
    """
    from services.s3_service import s3_service
    from workers.tasks import process_csv_file
    import io

    # Get analysis
    analysis = db.query(Analysis).filter(
        Analysis.analysis_id == analysis_id,
        Analysis.tenant_id == current_user.tenant_id
    ).first()

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )

    # Check if analysis is in correct status
    if analysis.status != AnalysisStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot upload CSV to analysis in {analysis.status} status. Analysis must be in PENDING status."
        )

    # Validate file type
    if not file.filename or not file.filename.endswith(('.csv', '.CSV')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV file"
        )

    # Read file content
    file_content = await file.read()
    file_size = len(file_content)

    # Validate file size (max 100MB)
    if file_size > 100 * 1024 * 1024:  # 100MB
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size must be less than 100MB"
        )

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty"
        )

    # Update analysis status to UPLOADING
    analysis.status = AnalysisStatus.UPLOADING
    db.commit()

    # Upload file to S3/MinIO
    object_key = s3_service.build_object_key(
        str(current_user.tenant_id),
        str(analysis.analysis_id),
        file.filename
    )

    try:
        s3_service.upload_file(
            io.BytesIO(file_content),
            object_key,
            file.content_type
        )

        # Update analysis with file path
        analysis.csv_file_path = object_key
        analysis.status = AnalysisStatus.PENDING
        db.commit()

    except Exception as e:
        # Revert status on error
        analysis.status = AnalysisStatus.FAILED
        analysis.error_message = f"Failed to upload file: {str(e)}"
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )

    # Queue CSV processing task
    task = process_csv_file.delay(
        str(analysis.analysis_id),
        object_key
    )

    return {
        "message": "File uploaded successfully",
        "analysis_id": str(analysis_id),
        "task_id": task.id,
        "status": analysis.status.value,
        "csv_file_path": analysis.csv_file_path
    }


@router.get("/{analysis_id}/status")
async def get_analysis_status(
    analysis_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current processing status of an analysis.

    Use this endpoint to poll for status updates during CSV processing.

    Returns:
    - **status**: Current processing status
    - **progress**: Processing progress percentage (if available)
    - **error_message**: Error details if status is FAILED
    """

    analysis = db.query(Analysis).filter(
        Analysis.analysis_id == analysis_id,
        Analysis.tenant_id == current_user.tenant_id
    ).first()

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )

    return {
        "analysis_id": str(analysis.analysis_id),
        "status": analysis.status.value,
        "error_message": analysis.error_message,
        "created_at": analysis.created_at,
        "updated_at": analysis.updated_at,
        "completed_at": analysis.completed_at
    }

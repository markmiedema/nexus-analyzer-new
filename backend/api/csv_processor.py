"""
CSV upload and processing API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
import uuid
import io

from database import get_db
from models.user import User
from models.analysis import Analysis, AnalysisStatus
from dependencies.auth import get_current_user
from services.s3_service import s3_service
from workers.tasks import process_csv_file
from config import settings

router = APIRouter()

# File validation constants
MAX_FILE_SIZE = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024  # Convert MB to bytes
ALLOWED_EXTENSIONS = settings.allowed_file_types_list
ALLOWED_MIME_TYPES = [
    'text/csv',
    'application/csv',
    'text/plain',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
]


def validate_file(file: UploadFile) -> None:
    """
    Validate uploaded file.

    Args:
        file: Uploaded file

    Raises:
        HTTPException: If validation fails
    """
    # Check file extension
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required"
        )

    file_ext = file.filename.split('.')[-1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Check MIME type (if provided)
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid content type: {file.content_type}"
        )


@router.post("/upload")
async def upload_csv(
    file: UploadFile = File(...),
    client_name: str = Form(...),
    period_start: str = Form(...),
    period_end: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload CSV file for processing.

    - **file**: CSV file to upload
    - **client_name**: Client/company name for this analysis
    - **period_start**: Start date of analysis period (YYYY-MM-DD)
    - **period_end**: End date of analysis period (YYYY-MM-DD)

    Returns analysis ID and task ID for tracking.
    """

    # Validate file
    validate_file(file)

    # Read file content
    file_content = await file.read()
    file_size = len(file_content)

    # Check file size
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE_MB}MB"
        )

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty"
        )

    # TODO: Add virus scanning placeholder
    # For production, integrate with ClamAV or similar

    # Create new analysis
    analysis = Analysis(
        analysis_id=uuid.uuid4(),
        tenant_id=current_user.tenant_id,
        created_by=current_user.user_id,
        client_name=client_name,
        period_start=period_start,
        period_end=period_end,
        status=AnalysisStatus.UPLOADING
    )

    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    # Upload file to S3
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
        # Rollback analysis creation if upload fails
        db.delete(analysis)
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
        "analysis_id": str(analysis.analysis_id),
        "task_id": task.id,
        "status": "queued",
        "message": "CSV file uploaded successfully and queued for processing"
    }


@router.get("/status/{analysis_id}")
async def get_processing_status(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get CSV processing status for an analysis.

    Returns current processing status and progress.
    """

    analysis = db.query(Analysis).filter(
        Analysis.analysis_id == analysis_id,
        Analysis.tenant_id == current_user.tenant_id  # Ensure same tenant
    ).first()

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )

    # Get transaction count
    from models.transaction import Transaction
    transaction_count = db.query(Transaction).filter(
        Transaction.analysis_id == analysis_id
    ).count()

    return {
        "analysis_id": str(analysis.analysis_id),
        "status": analysis.status.value,
        "client_name": analysis.client_name,
        "transaction_count": transaction_count,
        "error_message": analysis.error_message,
        "created_at": analysis.created_at,
        "completed_at": analysis.completed_at
    }


@router.get("/validation-report/{analysis_id}")
async def get_validation_report(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get validation report for a processed CSV.

    Returns validation errors and data quality metrics.
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

    if not analysis.validation_report_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Validation report not available"
        )

    # Download report from S3
    try:
        report_content = s3_service.download_file(analysis.validation_report_path)
        import json
        report = json.loads(report_content.decode('utf-8'))
        return report
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve validation report: {str(e)}"
        )


@router.get("/templates/download")
async def download_csv_template():
    """
    Download CSV template file.

    Returns a template CSV with all required and optional columns.
    """
    from fastapi.responses import StreamingResponse
    import csv as csv_module

    # Define template columns
    template_columns = [
        'date',
        'state',
        'amount',
        'tax_collected',
        'shipping_amount',
        'order_id',
        'customer_id',
        'marketplace',
        'product_category',
        'is_exempt'
    ]

    # Create CSV in memory
    output = io.StringIO()
    writer = csv_module.writer(output)

    # Write header
    writer.writerow(template_columns)

    # Write example rows
    writer.writerow([
        '2024-01-15',
        'CA',
        '100.00',
        '8.50',
        '5.00',
        'ORD-12345',
        'CUST-001',
        '',
        'Electronics',
        'FALSE'
    ])
    writer.writerow([
        '2024-01-16',
        'NY',
        '250.00',
        '20.00',
        '10.00',
        'ORD-12346',
        'CUST-002',
        'Amazon',
        'Apparel',
        'FALSE'
    ])

    # Reset stream position
    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=nexus_analyzer_template.csv"
        }
    )

"""
Report generation and download API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from pydantic import BaseModel
import io

from database import get_db
from models.user import User
from models.report import Report, ReportType
from models.analysis import Analysis
from dependencies.auth import get_current_user
from workers.tasks import generate_report
from services.s3_service import s3_service

router = APIRouter()


# ==================== Request Models ====================

class ReportGenerationRequest(BaseModel):
    """Request model for report generation."""
    report_type: str  # 'summary' or 'detailed'


# ==================== Report Generation Endpoints ====================

@router.post("/generate/{analysis_id}", status_code=status.HTTP_202_ACCEPTED)
async def generate_report_unified(
    analysis_id: UUID,
    request: ReportGenerationRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a report for an analysis.

    Accepts report_type in request body to determine which report to generate:
    - 'summary': Executive summary with key metrics and recommendations
    - 'detailed': Comprehensive analysis with full breakdown
    - 'compliance': Compliance-focused report (future)

    Returns task ID for tracking progress.
    """
    # Validate report type
    valid_types = ['summary', 'detailed', 'compliance']
    if request.report_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid report type. Must be one of: {', '.join(valid_types)}"
        )

    # Verify analysis exists and user has access
    analysis = db.query(Analysis).filter(
        Analysis.analysis_id == analysis_id,
        Analysis.tenant_id == current_user.tenant_id
    ).first()

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )

    # Check if analysis is complete
    if analysis.status.value not in ['completed', 'processing_nexus']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Analysis must be completed before generating reports"
        )

    # Queue report generation task
    task = generate_report.delay(
        str(analysis_id),
        report_type=request.report_type,
        include_branding=True
    )

    return {
        'analysis_id': str(analysis_id),
        'report_type': request.report_type,
        'task_id': task.id,
        'status': 'queued',
        'message': f'{request.report_type.capitalize()} report generation queued'
    }


@router.post("/generate/{analysis_id}/summary", status_code=status.HTTP_202_ACCEPTED)
async def generate_summary_report(
    analysis_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate executive summary report for an analysis.

    This creates a concise PDF report with:
    - Analysis overview
    - Key metrics
    - Nexus summary
    - Liability estimates
    - Priority recommendations

    Returns task ID for tracking progress.
    """
    # Verify analysis exists and user has access
    analysis = db.query(Analysis).filter(
        Analysis.analysis_id == analysis_id,
        Analysis.tenant_id == current_user.tenant_id
    ).first()

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )

    # Check if analysis is complete
    if analysis.status.value not in ['completed', 'processing_nexus']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Analysis must be completed before generating reports"
        )

    # Queue report generation task
    task = generate_report.delay(
        str(analysis_id),
        report_type='summary',
        include_branding=True
    )

    return {
        'analysis_id': str(analysis_id),
        'report_type': 'summary',
        'task_id': task.id,
        'status': 'queued',
        'message': 'Summary report generation queued'
    }


@router.post("/generate/{analysis_id}/detailed", status_code=status.HTTP_202_ACCEPTED)
async def generate_detailed_report(
    analysis_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate detailed analysis report for an analysis.

    This creates a comprehensive PDF report with:
    - Complete transaction summary
    - State-by-state nexus determination
    - Detailed liability breakdown
    - Methodology and assumptions
    - Full recommendations with action items

    Returns task ID for tracking progress.
    """
    # Verify analysis exists and user has access
    analysis = db.query(Analysis).filter(
        Analysis.analysis_id == analysis_id,
        Analysis.tenant_id == current_user.tenant_id
    ).first()

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )

    # Check if analysis is complete
    if analysis.status.value not in ['completed', 'processing_nexus']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Analysis must be completed before generating reports"
        )

    # Queue report generation task
    task = generate_report.delay(
        str(analysis_id),
        report_type='detailed',
        include_branding=True
    )

    return {
        'analysis_id': str(analysis_id),
        'report_type': 'detailed',
        'task_id': task.id,
        'status': 'queued',
        'message': 'Detailed report generation queued'
    }


# ==================== Report Retrieval Endpoints ====================

@router.get("/list/{analysis_id}", response_model=List[dict])
async def list_reports(
    analysis_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all reports for an analysis.

    Returns list of reports with metadata including:
    - Report ID
    - Report type (summary/detailed)
    - Generation date
    - File size
    """
    # Verify analysis exists and user has access
    analysis = db.query(Analysis).filter(
        Analysis.analysis_id == analysis_id,
        Analysis.tenant_id == current_user.tenant_id
    ).first()

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )

    # Get all reports for this analysis
    reports = db.query(Report).filter(
        Report.analysis_id == str(analysis_id)
    ).order_by(Report.created_at.desc()).all()

    return [
        {
            'report_id': str(report.report_id),
            'report_type': report.report_type.value,
            'file_path': report.file_path,
            'file_size': report.file_size,
            'created_at': report.created_at.isoformat() if report.created_at else None,
            'download_url': f"/api/v1/reports/download/{report.report_id}"
        }
        for report in reports
    ]


@router.get("/download/{report_id}")
async def download_report(
    report_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download a generated report.

    Returns PDF file for download.
    """
    # Get report
    report = db.query(Report).filter(
        Report.report_id == report_id
    ).first()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    # Verify user has access to this report's analysis
    analysis = db.query(Analysis).filter(
        Analysis.analysis_id == report.analysis_id,
        Analysis.tenant_id == current_user.tenant_id
    ).first()

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    # Download from S3
    try:
        pdf_content = s3_service.download_file(report.file_path)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve report: {str(e)}"
        )

    # Determine filename
    report_type_name = "summary" if report.report_type == ReportType.EXECUTIVE_SUMMARY else "detailed"
    filename = f"nexus_analysis_{report_type_name}_{analysis.client_name.replace(' ', '_')}_{report.created_at.strftime('%Y%m%d')}.pdf"

    # Return as streaming response
    return StreamingResponse(
        io.BytesIO(pdf_content),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/view/{report_id}")
async def view_report(
    report_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    View a report inline (opens in browser).

    Returns PDF file for viewing.
    """
    # Get report
    report = db.query(Report).filter(
        Report.report_id == report_id
    ).first()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    # Verify user has access
    analysis = db.query(Analysis).filter(
        Analysis.analysis_id == report.analysis_id,
        Analysis.tenant_id == current_user.tenant_id
    ).first()

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    # Download from S3
    try:
        pdf_content = s3_service.download_file(report.file_path)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve report: {str(e)}"
        )

    # Return for inline viewing
    return StreamingResponse(
        io.BytesIO(pdf_content),
        media_type="application/pdf",
        headers={
            "Content-Disposition": "inline"
        }
    )


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a report.

    Removes report from database and S3.
    """
    # Get report
    report = db.query(Report).filter(
        Report.report_id == report_id
    ).first()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    # Verify user has access
    analysis = db.query(Analysis).filter(
        Analysis.analysis_id == report.analysis_id,
        Analysis.tenant_id == current_user.tenant_id
    ).first()

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    # Delete from S3
    try:
        s3_service.delete_file(report.file_path)
    except Exception as e:
        # Log error but continue with database deletion
        import logging
        logging.error(f"Failed to delete report from S3: {e}")

    # Delete from database
    db.delete(report)
    db.commit()


# ==================== Report Email Endpoint ====================

@router.post("/email/{report_id}", status_code=status.HTTP_200_OK)
async def email_report(
    report_id: UUID,
    recipient_email: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Email a report to specified recipient.

    NOTE: This is a placeholder endpoint. Email functionality
    would require email service integration (SendGrid, AWS SES, etc.)

    Args:
        report_id: Report UUID
        recipient_email: Email address to send to

    Returns:
        Success message
    """
    # Get report
    report = db.query(Report).filter(
        Report.report_id == report_id
    ).first()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    # Verify user has access
    analysis = db.query(Analysis).filter(
        Analysis.analysis_id == report.analysis_id,
        Analysis.tenant_id == current_user.tenant_id
    ).first()

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )

    # TODO: Implement email sending
    # This would typically:
    # 1. Download report from S3
    # 2. Use email service (SendGrid, AWS SES, etc.)
    # 3. Send email with PDF attachment
    # 4. Log email send event

    # Placeholder response
    return {
        'message': 'Email functionality not yet implemented',
        'report_id': str(report_id),
        'recipient_email': recipient_email,
        'status': 'pending_implementation'
    }

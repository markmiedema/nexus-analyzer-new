"""
Analyses API endpoints for listing and managing analyses.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from database import get_db
from models.user import User
from models.analysis import Analysis
from dependencies.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=List[dict])
async def list_analyses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all analyses for the current user's tenant.

    Returns list of analyses with:
    - Analysis ID
    - Status
    - Created date
    - Completed date
    - Client name
    """
    # Get all analyses for the user's tenant
    analyses = db.query(Analysis).filter(
        Analysis.tenant_id == current_user.tenant_id
    ).order_by(Analysis.created_at.desc()).all()

    return [
        {
            'analysis_id': str(analysis.analysis_id),
            'status': analysis.status.value,
            'created_at': analysis.created_at.isoformat() if analysis.created_at else None,
            'completed_at': analysis.completed_at.isoformat() if analysis.completed_at else None,
            'client_name': analysis.client_name,
            'total_transactions': analysis.total_transactions,
            'total_revenue': float(analysis.total_revenue) if analysis.total_revenue else 0.0,
        }
        for analysis in analyses
    ]


@router.get("/{analysis_id}", response_model=dict)
async def get_analysis(
    analysis_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get details for a specific analysis.

    Returns full analysis details including:
    - Analysis metadata
    - Status
    - Transaction summary
    - Nexus results (if completed)
    """
    # Get the analysis
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
        'analysis_id': str(analysis.analysis_id),
        'status': analysis.status.value,
        'created_at': analysis.created_at.isoformat() if analysis.created_at else None,
        'completed_at': analysis.completed_at.isoformat() if analysis.completed_at else None,
        'client_name': analysis.client_name,
        'total_transactions': analysis.total_transactions,
        'total_revenue': float(analysis.total_revenue) if analysis.total_revenue else 0.0,
        'error_message': analysis.error_message,
    }


@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_analysis(
    analysis_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete an analysis and all associated data.

    This removes:
    - Analysis record
    - All transactions
    - All nexus results
    - All reports
    - CSV files from S3
    """
    # Get the analysis
    analysis = db.query(Analysis).filter(
        Analysis.analysis_id == analysis_id,
        Analysis.tenant_id == current_user.tenant_id
    ).first()

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )

    # TODO: Delete associated S3 files
    # TODO: Delete associated transactions, nexus results, reports

    # Delete the analysis
    db.delete(analysis)
    db.commit()

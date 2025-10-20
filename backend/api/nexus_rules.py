"""
Nexus rules and nexus results API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from database import get_db
from models.user import User
from models.nexus_rule import NexusRule
from models.nexus_result import NexusResult, NexusStatus
from models.analysis import Analysis
from dependencies.auth import get_current_user
from workers.tasks import run_nexus_determination

router = APIRouter()


# ==================== Nexus Rules Endpoints ====================

@router.get("/rules", response_model=List[dict])
async def get_all_nexus_rules(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all current nexus rules for all states.

    Returns economic nexus thresholds, measurement periods,
    and effective dates for all states with sales tax.
    """
    rules = db.query(NexusRule).filter(
        NexusRule.nexus_type == 'economic'
    ).order_by(NexusRule.state_code).all()

    return [
        {
            'rule_id': str(rule.rule_id),
            'state_code': rule.state_code,
            'nexus_type': rule.nexus_type,
            'sales_threshold': float(rule.sales_threshold) if rule.sales_threshold else None,
            'transaction_threshold': rule.transaction_threshold,
            'threshold_type': rule.threshold_type.value if rule.threshold_type else None,
            'measurement_period': rule.measurement_period.value if rule.measurement_period else None,
            'effective_date': rule.effective_date.isoformat() if rule.effective_date else None,
            'description': rule.description,
            'registration_threshold_days': rule.registration_threshold_days,
            'exclude_marketplace_sales': rule.exclude_marketplace_sales
        }
        for rule in rules
    ]


@router.get("/rules/{state}", response_model=dict)
async def get_state_nexus_rule(
    state: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get nexus rule for a specific state.

    Returns detailed economic nexus threshold information for the state.
    """
    state = state.upper()

    rule = db.query(NexusRule).filter(
        NexusRule.state_code == state,
        NexusRule.nexus_type == 'economic'
    ).first()

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No nexus rule found for state {state}"
        )

    return {
        'rule_id': str(rule.rule_id),
        'state_code': rule.state_code,
        'nexus_type': rule.nexus_type,
        'sales_threshold': float(rule.sales_threshold) if rule.sales_threshold else None,
        'transaction_threshold': rule.transaction_threshold,
        'threshold_type': rule.threshold_type.value if rule.threshold_type else None,
        'measurement_period': rule.measurement_period.value if rule.measurement_period else None,
        'effective_date': rule.effective_date.isoformat() if rule.effective_date else None,
        'description': rule.description,
        'registration_threshold_days': rule.registration_threshold_days,
        'exclude_marketplace_sales': rule.exclude_marketplace_sales
    }


# ==================== Nexus Results Endpoints ====================

@router.get("/results/{analysis_id}", response_model=List[dict])
async def get_nexus_results(
    analysis_id: UUID,
    nexus_status: Optional[str] = Query(None, description="Filter by nexus status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get nexus determination results for an analysis.

    Returns nexus status for all states, including:
    - Physical and economic nexus determination
    - Sales and transaction counts
    - Threshold comparison
    - Confidence levels
    - Recommendations

    Query Parameters:
    - nexus_status: Filter by status (nexus_physical, nexus_economic, close_to_threshold, no_nexus)
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

    # Build query
    query = db.query(NexusResult).filter(
        NexusResult.analysis_id == str(analysis_id)
    )

    # Apply status filter if provided
    if nexus_status:
        try:
            status_enum = NexusStatus(nexus_status)
            query = query.filter(NexusResult.nexus_status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid nexus status: {nexus_status}"
            )

    results = query.order_by(NexusResult.state).all()

    return [
        {
            'result_id': str(result.result_id),
            'state': result.state,
            'nexus_status': result.nexus_status.value,
            'nexus_date': result.nexus_date.isoformat() if result.nexus_date else None,
            'physical_nexus': result.physical_nexus,
            'economic_nexus': result.economic_nexus,
            'total_sales': result.total_sales,
            'taxable_sales': result.taxable_sales,
            'transaction_count': result.transaction_count,
            'sales_threshold': float(result.sales_threshold) if result.sales_threshold else None,
            'transaction_threshold': result.transaction_threshold,
            'threshold_type': result.threshold_type,
            'measurement_period': result.measurement_period,
            'confidence_level': result.confidence_level.value if result.confidence_level else None,
            'registration_deadline': result.registration_deadline.isoformat() if result.registration_deadline else None,
            'close_to_threshold': result.close_to_threshold,
            'threshold_percentage': result.threshold_percentage,
            'days_until_threshold': result.days_until_threshold,
            'recommendation': result.recommendation,
            'calculation_notes': result.calculation_notes,
            'calculated_at': result.calculated_at.isoformat() if result.calculated_at else None
        }
        for result in results
    ]


@router.get("/results/{analysis_id}/summary", response_model=dict)
async def get_nexus_summary(
    analysis_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get summarized nexus determination results.

    Returns high-level summary including:
    - Count of states with nexus
    - Count of states close to threshold
    - List of states requiring registration
    - Priority recommendations
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

    # Get all results
    results = db.query(NexusResult).filter(
        NexusResult.analysis_id == str(analysis_id)
    ).all()

    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No nexus results found for this analysis. Run nexus determination first."
        )

    # Categorize results
    physical_nexus_states = []
    economic_nexus_states = []
    close_to_threshold_states = []
    no_nexus_states = []

    for result in results:
        if result.nexus_status == NexusStatus.NEXUS_PHYSICAL:
            physical_nexus_states.append(result.state)
        elif result.nexus_status == NexusStatus.NEXUS_ECONOMIC:
            economic_nexus_states.append(result.state)
        elif result.nexus_status == NexusStatus.CLOSE_TO_THRESHOLD:
            close_to_threshold_states.append(result.state)
        else:
            no_nexus_states.append(result.state)

    # Get states requiring registration
    from datetime import date
    today = date.today()

    urgent_states = []
    upcoming_deadlines = []

    for result in results:
        if result.registration_deadline:
            if result.registration_deadline < today:
                urgent_states.append({
                    'state': result.state,
                    'deadline': result.registration_deadline.isoformat(),
                    'days_overdue': (today - result.registration_deadline).days
                })
            elif result.registration_deadline <= today + timedelta(days=30):
                upcoming_deadlines.append({
                    'state': result.state,
                    'deadline': result.registration_deadline.isoformat(),
                    'days_remaining': (result.registration_deadline - today).days
                })

    return {
        'analysis_id': str(analysis_id),
        'total_states_analyzed': len(results),
        'nexus_breakdown': {
            'physical_nexus': len(physical_nexus_states),
            'economic_nexus': len(economic_nexus_states),
            'close_to_threshold': len(close_to_threshold_states),
            'no_nexus': len(no_nexus_states)
        },
        'states_with_nexus': sorted(physical_nexus_states + economic_nexus_states),
        'physical_nexus_states': sorted(physical_nexus_states),
        'economic_nexus_states': sorted(economic_nexus_states),
        'close_to_threshold_states': sorted(close_to_threshold_states),
        'urgent_registrations': urgent_states,
        'upcoming_deadlines': sorted(upcoming_deadlines, key=lambda x: x['deadline'])
    }


@router.get("/results/{analysis_id}/states/{state}", response_model=dict)
async def get_state_nexus_result(
    analysis_id: UUID,
    state: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get nexus determination result for a specific state.

    Returns detailed nexus information including calculations,
    thresholds, and recommendations for the state.
    """
    state = state.upper()

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

    # Get result for state
    result = db.query(NexusResult).filter(
        NexusResult.analysis_id == str(analysis_id),
        NexusResult.state == state
    ).first()

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No nexus result found for state {state}"
        )

    return {
        'result_id': str(result.result_id),
        'state': result.state,
        'nexus_status': result.nexus_status.value,
        'nexus_date': result.nexus_date.isoformat() if result.nexus_date else None,
        'physical_nexus': result.physical_nexus,
        'economic_nexus': result.economic_nexus,
        'total_sales': result.total_sales,
        'taxable_sales': result.taxable_sales,
        'transaction_count': result.transaction_count,
        'sales_threshold': float(result.sales_threshold) if result.sales_threshold else None,
        'transaction_threshold': result.transaction_threshold,
        'threshold_type': result.threshold_type,
        'measurement_period': result.measurement_period,
        'confidence_level': result.confidence_level.value if result.confidence_level else None,
        'registration_deadline': result.registration_deadline.isoformat() if result.registration_deadline else None,
        'close_to_threshold': result.close_to_threshold,
        'threshold_percentage': result.threshold_percentage,
        'days_until_threshold': result.days_until_threshold,
        'recommendation': result.recommendation,
        'calculation_notes': result.calculation_notes,
        'calculated_at': result.calculated_at.isoformat() if result.calculated_at else None
    }


@router.post("/run/{analysis_id}", status_code=status.HTTP_202_ACCEPTED)
async def trigger_nexus_determination(
    analysis_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Trigger nexus determination for an analysis.

    This queues an asynchronous task to run the complete nexus
    determination process. Results will be available via the
    /results/{analysis_id} endpoint once processing is complete.

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

    # Check if analysis has transactions
    from models.transaction import Transaction
    transaction_count = db.query(Transaction).filter(
        Transaction.analysis_id == str(analysis_id)
    ).count()

    if transaction_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No transactions found for analysis. Upload and process CSV first."
        )

    # Queue nexus determination task
    task = run_nexus_determination.delay(str(analysis_id))

    return {
        'analysis_id': str(analysis_id),
        'task_id': task.id,
        'status': 'queued',
        'message': 'Nexus determination queued for processing'
    }


# Import timedelta for deadline calculations
from datetime import timedelta

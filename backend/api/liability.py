"""
Liability estimation API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

from database import get_db
from models.user import User
from models.liability_estimate import LiabilityEstimate, RiskLevel
from models.analysis import Analysis
from dependencies.auth import get_current_user
from workers.tasks import calculate_liability

router = APIRouter()


# ==================== Request/Response Models ====================

class LiabilityCalculationRequest(BaseModel):
    """Request model for custom liability calculation."""
    exemption_rate: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Exemption rate (0.0-1.0, e.g., 0.10 for 10%)"
    )
    include_penalties: bool = Field(
        True,
        description="Whether to include penalty calculations"
    )
    custom_lookback_months: Optional[int] = Field(
        None,
        ge=0,
        le=48,
        description="Custom lookback period in months (0-48)"
    )


# ==================== Liability Estimates Endpoints ====================

@router.get("/estimates/{analysis_id}", response_model=List[dict])
async def get_liability_estimates(
    analysis_id: UUID,
    risk_level: Optional[str] = Query(None, description="Filter by risk level (high, medium, low)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get liability estimates for an analysis.

    Returns estimated sales tax liability for all states with nexus, including:
    - Taxable sales calculations
    - Liability ranges (low, mid, high estimates)
    - Lookback period estimates
    - Penalty and interest calculations
    - Risk assessments
    - Recommendations

    Query Parameters:
    - risk_level: Filter by risk level (high, medium, low)
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
    query = db.query(LiabilityEstimate).filter(
        LiabilityEstimate.analysis_id == str(analysis_id)
    )

    # Apply risk filter if provided
    if risk_level:
        try:
            risk_enum = RiskLevel(risk_level)
            query = query.filter(LiabilityEstimate.risk_level == risk_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid risk level: {risk_level}"
            )

    estimates = query.order_by(
        LiabilityEstimate.estimated_liability_mid.desc()
    ).all()

    return [
        {
            'estimate_id': str(estimate.estimate_id),
            'state': estimate.state,
            'period_start': estimate.period_start.isoformat() if estimate.period_start else None,
            'period_end': estimate.period_end.isoformat() if estimate.period_end else None,
            'gross_sales': estimate.gross_sales,
            'exempt_sales': estimate.exempt_sales,
            'marketplace_sales': estimate.marketplace_sales,
            'taxable_sales': estimate.taxable_sales,
            'state_tax_rate': estimate.state_tax_rate,
            'avg_local_tax_rate': estimate.avg_local_tax_rate,
            'estimated_liability_low': estimate.estimated_liability_low,
            'estimated_liability_mid': estimate.estimated_liability_mid,
            'estimated_liability': estimate.estimated_liability_mid,
            'estimated_liability_high': estimate.estimated_liability_high,
            'lookback_period_months': estimate.lookback_period_months,
            'lookback_start_date': estimate.lookback_start_date.isoformat() if estimate.lookback_start_date else None,
            'lookback_end_date': estimate.lookback_end_date.isoformat() if estimate.lookback_end_date else None,
            'lookback_liability_estimate': estimate.lookback_liability_estimate,
            'penalty_amount': estimate.penalty_amount,
            'interest_amount': estimate.interest_amount,
            'total_liability_with_penalties': estimate.total_liability_with_penalties,
            'exemption_rate_assumed': estimate.exemption_rate_assumed,
            'risk_level': estimate.risk_level.value if estimate.risk_level else None,
            'recommendation': estimate.recommendation,
            'calculation_assumptions': estimate.calculation_assumptions,
            'calculated_at': estimate.calculated_at.isoformat() if estimate.calculated_at else None
        }
        for estimate in estimates
    ]


@router.get("/estimates/{analysis_id}/summary", response_model=dict)
async def get_liability_summary(
    analysis_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get summarized liability estimates.

    Returns high-level summary including:
    - Total liability across all states
    - Breakdown by risk level
    - States with highest liability
    - Total penalties if applicable
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

    # Get all estimates
    estimates = db.query(LiabilityEstimate).filter(
        LiabilityEstimate.analysis_id == str(analysis_id)
    ).all()

    if not estimates:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No liability estimates found. Run liability calculation first."
        )

    # Calculate totals
    total_liability_low = sum(est.estimated_liability_low or 0 for est in estimates)
    total_liability_mid = sum(est.estimated_liability_mid or 0 for est in estimates)
    total_liability_high = sum(est.estimated_liability_high or 0 for est in estimates)
    total_lookback_liability = sum(est.lookback_liability_estimate or 0 for est in estimates)
    total_penalties = sum(est.penalty_amount or 0 for est in estimates)
    total_interest = sum(est.interest_amount or 0 for est in estimates)

    # Categorize by risk
    high_risk_states = []
    medium_risk_states = []
    low_risk_states = []

    for est in estimates:
        state_info = {
            'state': est.state,
            'liability': est.estimated_liability_mid,
            'risk_level': est.risk_level.value if est.risk_level else None
        }

        if est.risk_level == RiskLevel.HIGH:
            high_risk_states.append(state_info)
        elif est.risk_level == RiskLevel.MEDIUM:
            medium_risk_states.append(state_info)
        else:
            low_risk_states.append(state_info)

    # Top 5 states by liability
    top_states = sorted(
        estimates,
        key=lambda e: e.estimated_liability_mid or 0,
        reverse=True
    )[:5]

    top_states_list = [
        {
            'state': est.state,
            'liability_mid': est.estimated_liability_mid,
            'liability_range': {
                'low': est.estimated_liability_low,
                'high': est.estimated_liability_high
            },
            'risk_level': est.risk_level.value if est.risk_level else None
        }
        for est in top_states
    ]

    # Priority recommendations
    priority_actions = []

    if high_risk_states:
        priority_actions.append(f"Address {len(high_risk_states)} high-risk states immediately")

    if total_penalties > 0:
        priority_actions.append(f"Penalties accruing: ${total_penalties:,.2f} - consider VDA")

    if total_liability_mid > 100000:
        priority_actions.append("Significant total liability - prioritize compliance plan")

    return {
        'analysis_id': str(analysis_id),
        'total_states': len(estimates),
        'total_liability': {
            'low_estimate': total_liability_low,
            'mid_estimate': total_liability_mid,
            'high_estimate': total_liability_high
        },
        'lookback_liability_total': total_lookback_liability,
        'penalties_and_interest': {
            'total_penalties': total_penalties,
            'total_interest': total_interest,
            'combined': total_penalties + total_interest
        },
        'risk_breakdown': {
            'high_risk': len(high_risk_states),
            'medium_risk': len(medium_risk_states),
            'low_risk': len(low_risk_states)
        },
        'high_risk_states': [s['state'] for s in high_risk_states],
        'top_liability_states': top_states_list,
        'priority_actions': priority_actions
    }


@router.get("/estimates/{analysis_id}/states/{state}", response_model=dict)
async def get_state_liability_estimate(
    analysis_id: UUID,
    state: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get liability estimate for a specific state.

    Returns detailed liability information including all calculations,
    assumptions, and recommendations for the state.
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

    # Get estimate for state
    estimate = db.query(LiabilityEstimate).filter(
        LiabilityEstimate.analysis_id == str(analysis_id),
        LiabilityEstimate.state == state
    ).first()

    if not estimate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No liability estimate found for state {state}"
        )

    return {
        'estimate_id': str(estimate.estimate_id),
        'state': estimate.state,
        'period_start': estimate.period_start.isoformat() if estimate.period_start else None,
        'period_end': estimate.period_end.isoformat() if estimate.period_end else None,
        'gross_sales': estimate.gross_sales,
        'exempt_sales': estimate.exempt_sales,
        'marketplace_sales': estimate.marketplace_sales,
        'taxable_sales': estimate.taxable_sales,
        'state_tax_rate': estimate.state_tax_rate,
        'avg_local_tax_rate': estimate.avg_local_tax_rate,
        'estimated_liability_low': estimate.estimated_liability_low,
        'estimated_liability_mid': estimate.estimated_liability_mid,
        'estimated_liability': estimate.estimated_liability_mid,
        'estimated_liability_high': estimate.estimated_liability_high,
        'lookback_period_months': estimate.lookback_period_months,
        'lookback_start_date': estimate.lookback_start_date.isoformat() if estimate.lookback_start_date else None,
        'lookback_end_date': estimate.lookback_end_date.isoformat() if estimate.lookback_end_date else None,
        'lookback_liability_estimate': estimate.lookback_liability_estimate,
        'penalty_amount': estimate.penalty_amount,
        'interest_amount': estimate.interest_amount,
        'total_liability_with_penalties': estimate.total_liability_with_penalties,
        'exemption_rate_assumed': estimate.exemption_rate_assumed,
        'risk_level': estimate.risk_level.value if estimate.risk_level else None,
        'recommendation': estimate.recommendation,
        'calculation_assumptions': estimate.calculation_assumptions,
        'calculated_at': estimate.calculated_at.isoformat() if estimate.calculated_at else None
    }


@router.post("/calculate/{analysis_id}", status_code=status.HTTP_202_ACCEPTED)
async def trigger_liability_calculation(
    analysis_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Trigger liability calculation for an analysis.

    This queues an asynchronous task to calculate liability estimates
    for all states with nexus. Uses default assumptions (10% exemption rate).

    Results will be available via /estimates/{analysis_id} once complete.

    Note: Nexus determination must be run first.

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

    # Check if nexus results exist
    from models.nexus_result import NexusResult, NexusStatus
    nexus_count = db.query(NexusResult).filter(
        NexusResult.analysis_id == str(analysis_id),
        NexusResult.nexus_status.in_([
            NexusStatus.NEXUS_PHYSICAL,
            NexusStatus.NEXUS_ECONOMIC
        ])
    ).count()

    if nexus_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No nexus results found. Run nexus determination first."
        )

    # Queue liability calculation task
    task = calculate_liability.delay(str(analysis_id))

    return {
        'analysis_id': str(analysis_id),
        'task_id': task.id,
        'status': 'queued',
        'message': 'Liability calculation queued for processing'
    }


@router.post("/recalculate/{analysis_id}", status_code=status.HTTP_202_ACCEPTED)
async def recalculate_liability_with_assumptions(
    analysis_id: UUID,
    request: LiabilityCalculationRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Recalculate liability with custom assumptions.

    Allows specification of:
    - Custom exemption rate (default 10%)
    - Whether to include penalties
    - Custom lookback period in months

    This is useful for scenario analysis and sensitivity testing.

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

    # Check if nexus results exist
    from models.nexus_result import NexusResult, NexusStatus
    nexus_count = db.query(NexusResult).filter(
        NexusResult.analysis_id == str(analysis_id),
        NexusResult.nexus_status.in_([
            NexusStatus.NEXUS_PHYSICAL,
            NexusStatus.NEXUS_ECONOMIC
        ])
    ).count()

    if nexus_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No nexus results found. Run nexus determination first."
        )

    # Queue liability calculation task with custom parameters
    task = calculate_liability.delay(
        str(analysis_id),
        exemption_rate=request.exemption_rate,
        include_penalties=request.include_penalties,
        custom_lookback_months=request.custom_lookback_months
    )

    return {
        'analysis_id': str(analysis_id),
        'task_id': task.id,
        'status': 'queued',
        'message': 'Liability recalculation queued with custom assumptions',
        'assumptions': {
            'exemption_rate': request.exemption_rate,
            'include_penalties': request.include_penalties,
            'custom_lookback_months': request.custom_lookback_months
        }
    }

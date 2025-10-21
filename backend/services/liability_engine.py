"""
Liability estimation engine for sales tax liability calculations.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Optional, List, Tuple
from datetime import date, datetime
from decimal import Decimal
from dateutil.relativedelta import relativedelta
import logging

from models.nexus_result import NexusResult, NexusDetermination
from models.transaction import Transaction
from models.state_tax_config import StateTaxConfig
from models.liability_estimate import LiabilityEstimate, RiskLevel
from models.analysis import Analysis

logger = logging.getLogger(__name__)

# Default assumptions
DEFAULT_EXEMPTION_RATE = 0.10  # Conservative 10% exemption assumption
DEFAULT_PENALTY_RATE = 0.10  # 10% penalty for late registration
MONTHLY_INTEREST_RATE = 0.01  # 1% monthly interest (12% annual)

# Lookback period defaults by state (in months)
DEFAULT_LOOKBACK_MONTHS = 36  # 3 years is common
MAX_LOOKBACK_MONTHS = 48  # 4 years maximum


class LiabilityEngine:
    """Engine for estimating sales tax liability."""

    def __init__(self, db: Session):
        """
        Initialize liability engine.

        Args:
            db: Database session
        """
        self.db = db

    def calculate_liability(
        self,
        analysis_id: str,
        exemption_rate: Optional[float] = None,
        include_penalties: bool = True,
        custom_lookback_months: Optional[int] = None
    ) -> List[LiabilityEstimate]:
        """
        Calculate liability estimates for all states with nexus.

        Args:
            analysis_id: Analysis UUID
            exemption_rate: Custom exemption rate (defaults to 10%)
            include_penalties: Whether to include penalty estimates
            custom_lookback_months: Custom lookback period in months

        Returns:
            List of LiabilityEstimate objects
        """
        logger.info(f"Calculating liability for analysis {analysis_id}")

        if exemption_rate is None:
            exemption_rate = DEFAULT_EXEMPTION_RATE

        # Get analysis
        analysis = self.db.query(Analysis).filter(
            Analysis.analysis_id == analysis_id
        ).first()

        if not analysis:
            raise ValueError(f"Analysis {analysis_id} not found")

        # Get nexus results for states with nexus
        nexus_results = self.db.query(NexusResult).filter(
            NexusResult.analysis_id == analysis_id,
            NexusResult.overall_determination.in_([
                NexusDetermination.NEXUS_PHYSICAL,
                NexusDetermination.NEXUS_ECONOMIC
            ])
        ).all()

        logger.info(f"Calculating liability for {len(nexus_results)} states with nexus")

        liability_estimates = []

        for nexus_result in nexus_results:
            state = nexus_result.state

            # Get state tax config
            tax_config = self.db.query(StateTaxConfig).filter(
                StateTaxConfig.state_code == state
            ).first()

            if not tax_config or not tax_config.has_sales_tax:
                logger.warning(f"No tax config for {state}, skipping")
                continue

            # Calculate period liability
            period_liability = self._calculate_period_liability(
                analysis_id,
                state,
                tax_config,
                analysis.period_start,
                analysis.period_end,
                exemption_rate
            )

            # Calculate lookback period liability
            lookback_months = custom_lookback_months or self._determine_lookback_period(
                state,
                nexus_result.nexus_date
            )

            lookback_liability = None
            lookback_start_date = None
            lookback_end_date = None

            if nexus_result.nexus_date and lookback_months > 0:
                lookback_start_date, lookback_end_date = self._calculate_lookback_dates(
                    nexus_result.nexus_date,
                    lookback_months
                )

                lookback_liability = self._calculate_period_liability(
                    analysis_id,
                    state,
                    tax_config,
                    lookback_start_date,
                    lookback_end_date,
                    exemption_rate
                )

            # Calculate penalties if applicable
            penalty_amount = None
            interest_amount = None
            total_liability_with_penalties = None

            if include_penalties and nexus_result.registration_deadline:
                if date.today() > nexus_result.registration_deadline:
                    # Calculate penalties for late registration
                    penalty_amount, interest_amount = self._calculate_penalties(
                        period_liability['mid_estimate'],
                        nexus_result.registration_deadline,
                        date.today()
                    )

                    total_liability_with_penalties = (
                        period_liability['mid_estimate'] +
                        penalty_amount +
                        interest_amount
                    )

            # Calculate risk assessment
            risk_level = self._assess_risk(
                state,
                period_liability['mid_estimate'],
                nexus_result.overall_determination,
                nexus_result.confidence_level,
                bool(penalty_amount)
            )

            # Generate recommendations
            recommendation = self._generate_liability_recommendation(
                risk_level,
                period_liability['mid_estimate'],
                penalty_amount,
                nexus_result.overall_determination
            )

            # Build assumptions note
            assumptions = self._build_assumptions_note(
                exemption_rate,
                tax_config,
                lookback_months
            )

            # Create liability estimate
            estimate = LiabilityEstimate(
                analysis_id=analysis_id,
                state=state,
                nexus_result_id=nexus_result.result_id,
                period_start=analysis.period_start,
                period_end=analysis.period_end,
                gross_sales=period_liability['gross_sales'],
                exempt_sales=period_liability['exempt_sales'],
                marketplace_sales=period_liability['marketplace_sales'],
                taxable_sales=period_liability['taxable_sales'],
                state_tax_rate=float(tax_config.state_tax_rate),
                avg_local_tax_rate=float(tax_config.avg_local_tax_rate) if tax_config.avg_local_tax_rate else None,
                estimated_liability_low=period_liability['low_estimate'],
                estimated_liability_mid=period_liability['mid_estimate'],
                estimated_liability_high=period_liability['high_estimate'],
                lookback_period_months=lookback_months,
                lookback_start_date=lookback_start_date,
                lookback_end_date=lookback_end_date,
                lookback_liability_estimate=lookback_liability['mid_estimate'] if lookback_liability else None,
                penalty_amount=float(penalty_amount) if penalty_amount else None,
                interest_amount=float(interest_amount) if interest_amount else None,
                total_liability_with_penalties=float(total_liability_with_penalties) if total_liability_with_penalties else None,
                exemption_rate_assumed=float(exemption_rate),
                risk_level=risk_level,
                recommendation=recommendation,
                calculation_assumptions=assumptions
            )

            liability_estimates.append(estimate)
            self.db.add(estimate)

        # Commit all estimates
        self.db.commit()

        logger.info(f"Liability calculation complete: {len(liability_estimates)} states processed")
        return liability_estimates

    def _calculate_period_liability(
        self,
        analysis_id: str,
        state: str,
        tax_config: StateTaxConfig,
        period_start: date,
        period_end: date,
        exemption_rate: float
    ) -> Dict:
        """
        Calculate liability for a specific period.

        Args:
            analysis_id: Analysis UUID
            state: State code
            tax_config: State tax configuration
            period_start: Period start date
            period_end: Period end date
            exemption_rate: Exemption rate to apply

        Returns:
            Dict with liability calculations
        """
        # Get transactions for the state in the period
        transactions = self.db.query(Transaction).filter(
            Transaction.analysis_id == analysis_id,
            Transaction.customer_state == state,
            Transaction.transaction_date >= period_start,
            Transaction.transaction_date <= period_end
        ).all()

        # Calculate sales breakdowns
        gross_sales = Decimal('0')
        exempt_sales = Decimal('0')
        marketplace_sales = Decimal('0')

        for txn in transactions:
            gross_sales += txn.gross_amount

            # Track explicitly exempt sales
            if txn.is_exempt_sale:
                exempt_sales += txn.gross_amount

            # Track marketplace facilitator sales
            if txn.is_marketplace_sale:
                marketplace_sales += txn.gross_amount

        # Calculate taxable sales base
        # Subtract marketplace (facilitator collects) and explicit exemptions
        potentially_taxable = gross_sales - marketplace_sales - exempt_sales

        # Apply additional exemption rate assumption to remaining sales
        # This accounts for unidentified exempt sales (resale certs, etc.)
        additional_exempt = potentially_taxable * Decimal(str(exemption_rate))
        taxable_sales = potentially_taxable - additional_exempt

        # Ensure non-negative
        taxable_sales = max(taxable_sales, Decimal('0'))

        # Calculate liability estimates
        state_rate = Decimal(str(tax_config.state_tax_rate)) / Decimal('100')
        avg_local_rate = Decimal(str(tax_config.avg_local_tax_rate or 0)) / Decimal('100')

        # Low estimate: State rate only
        low_estimate = taxable_sales * state_rate

        # Mid estimate: State rate + 50% of average local rate
        mid_rate = state_rate + (avg_local_rate * Decimal('0.5'))
        mid_estimate = taxable_sales * mid_rate

        # High estimate: State rate + full average local rate
        high_rate = state_rate + avg_local_rate
        high_estimate = taxable_sales * high_rate

        return {
            'gross_sales': float(gross_sales),
            'exempt_sales': float(exempt_sales),
            'marketplace_sales': float(marketplace_sales),
            'taxable_sales': float(taxable_sales),
            'low_estimate': float(low_estimate),
            'mid_estimate': float(mid_estimate),
            'high_estimate': float(high_estimate),
            'effective_rate_low': float(state_rate * 100),
            'effective_rate_mid': float(mid_rate * 100),
            'effective_rate_high': float(high_rate * 100)
        }

    def _determine_lookback_period(
        self,
        state: str,
        nexus_date: Optional[date]
    ) -> int:
        """
        Determine appropriate lookback period in months.

        Args:
            state: State code
            nexus_date: Date when nexus was established

        Returns:
            Lookback period in months
        """
        if not nexus_date:
            return 0

        # Calculate months since nexus establishment
        today = date.today()
        months_since_nexus = (
            (today.year - nexus_date.year) * 12 +
            (today.month - nexus_date.month)
        )

        # Most states have 3-year lookback for sales tax
        # Cap at 4 years maximum
        lookback_months = min(months_since_nexus, DEFAULT_LOOKBACK_MONTHS)
        lookback_months = min(lookback_months, MAX_LOOKBACK_MONTHS)

        return max(0, lookback_months)

    def _calculate_lookback_dates(
        self,
        nexus_date: date,
        lookback_months: int
    ) -> Tuple[date, date]:
        """
        Calculate lookback period start and end dates.

        Args:
            nexus_date: Date when nexus was established
            lookback_months: Number of months to look back

        Returns:
            Tuple of (start_date, end_date)
        """
        # Lookback period is from nexus date back N months
        start_date = nexus_date - relativedelta(months=lookback_months)
        end_date = nexus_date

        return start_date, end_date

    def _calculate_penalties(
        self,
        liability_amount: float,
        registration_deadline: date,
        current_date: date
    ) -> Tuple[Decimal, Decimal]:
        """
        Calculate penalty and interest for late registration.

        Args:
            liability_amount: Estimated liability amount
            registration_deadline: Required registration deadline
            current_date: Current date

        Returns:
            Tuple of (penalty_amount, interest_amount)
        """
        if current_date <= registration_deadline:
            return Decimal('0'), Decimal('0')

        liability = Decimal(str(liability_amount))

        # Calculate base penalty (typically 10% of liability)
        penalty = liability * Decimal(str(DEFAULT_PENALTY_RATE))

        # Calculate interest (1% per month)
        months_late = (
            (current_date.year - registration_deadline.year) * 12 +
            (current_date.month - registration_deadline.month)
        )

        # Interest compounds monthly
        interest = liability * Decimal(str(MONTHLY_INTEREST_RATE)) * Decimal(str(months_late))

        return penalty, interest

    def _assess_risk(
        self,
        state: str,
        liability_amount: float,
        nexus_status: NexusDetermination,
        confidence_level: Optional[str],
        has_penalties: bool
    ) -> RiskLevel:
        """
        Assess risk level for the liability.

        Args:
            state: State code
            liability_amount: Estimated liability
            nexus_status: Type of nexus
            confidence_level: Confidence in nexus determination
            has_penalties: Whether penalties are accruing

        Returns:
            RiskLevel enum value
        """
        # High risk factors
        high_risk_factors = 0

        # Physical nexus is higher risk than economic
        if nexus_status == NexusDetermination.NEXUS_PHYSICAL:
            high_risk_factors += 2

        # High liability amounts increase risk
        if liability_amount > 50000:
            high_risk_factors += 2
        elif liability_amount > 10000:
            high_risk_factors += 1

        # Penalties accruing is high risk
        if has_penalties:
            high_risk_factors += 3

        # Low confidence in nexus determination reduces risk
        if confidence_level == 'low':
            high_risk_factors -= 1

        # Determine risk level
        if high_risk_factors >= 5:
            return RiskLevel.HIGH
        elif high_risk_factors >= 3:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def _generate_liability_recommendation(
        self,
        risk_level: RiskLevel,
        liability_amount: float,
        penalty_amount: Optional[float],
        nexus_status: NexusDetermination
    ) -> str:
        """
        Generate recommendation based on liability and risk.

        Args:
            risk_level: Assessed risk level
            liability_amount: Estimated liability
            penalty_amount: Penalty amount if applicable
            nexus_status: Type of nexus

        Returns:
            Recommendation string
        """
        recommendations = []

        # Risk-based recommendations
        if risk_level == RiskLevel.HIGH:
            recommendations.append("HIGH RISK: Consult with sales tax professional immediately.")

            if penalty_amount:
                recommendations.append("Penalties are accruing. Consider Voluntary Disclosure Agreement (VDA).")

        elif risk_level == RiskLevel.MEDIUM:
            recommendations.append("MEDIUM RISK: Review with tax advisor and consider filing options.")

        # Liability amount recommendations
        if liability_amount > 50000:
            recommendations.append(f"Significant liability (${liability_amount:,.2f}). Priority state for compliance.")
        elif liability_amount > 10000:
            recommendations.append(f"Moderate liability (${liability_amount:,.2f}). Plan for registration and filing.")

        # Nexus type recommendations
        if nexus_status == NexusDetermination.NEXUS_PHYSICAL:
            recommendations.append("Physical presence creates strong nexus obligation.")

        # Default recommendation if low risk
        if not recommendations:
            recommendations.append("Register and begin collecting sales tax prospectively.")

        return " ".join(recommendations)

    def _build_assumptions_note(
        self,
        exemption_rate: float,
        tax_config: StateTaxConfig,
        lookback_months: int
    ) -> str:
        """
        Build detailed assumptions note.

        Args:
            exemption_rate: Exemption rate used
            tax_config: State tax configuration
            lookback_months: Lookback period

        Returns:
            Assumptions note string
        """
        notes = []

        notes.append(f"Exemption rate: {exemption_rate * 100:.0f}% assumed for unknown exemptions")
        notes.append(f"State rate: {tax_config.state_tax_rate}%")

        if tax_config.avg_local_tax_rate:
            notes.append(f"Avg local rate: {tax_config.avg_local_tax_rate}%")
            notes.append("Low estimate uses state rate only")
            notes.append("Mid estimate uses state + 50% avg local")
            notes.append("High estimate uses state + full avg local")
        else:
            notes.append("No local sales tax in this state")

        if lookback_months > 0:
            years = lookback_months / 12
            notes.append(f"Lookback period: {lookback_months} months ({years:.1f} years)")

        notes.append("Estimates are approximations only - actual liability may vary")
        notes.append("Consult with tax professional for accurate assessment")

        return "; ".join(notes)


# Create global instance factory
def create_liability_engine(db: Session) -> LiabilityEngine:
    """Create liability engine instance with database session."""
    return LiabilityEngine(db)

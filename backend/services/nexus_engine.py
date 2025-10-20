"""
Nexus determination engine for sales tax nexus analysis.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Tuple, Optional
from datetime import date, datetime, timedelta
from decimal import Decimal
import logging
from dateutil.relativedelta import relativedelta

from models.business_profile import BusinessProfile
from models.transaction import Transaction
from models.nexus_rule import NexusRule, ThresholdType, MeasurementPeriod
from models.nexus_result import NexusResult, NexusStatus, ConfidenceLevel
from models.analysis import Analysis
from services.business_profile_service import business_profile_service

logger = logging.getLogger(__name__)


# Threshold warning percentage (e.g., 80% = warn when at 80% of threshold)
THRESHOLD_WARNING_PERCENTAGE = 0.80


class NexusEngine:
    """Engine for determining sales tax nexus."""

    def __init__(self, db: Session):
        """
        Initialize nexus engine.

        Args:
            db: Database session
        """
        self.db = db

    def determine_nexus(
        self,
        analysis_id: str,
        business_profile: Optional[BusinessProfile] = None
    ) -> List[NexusResult]:
        """
        Run complete nexus determination for an analysis.

        Args:
            analysis_id: Analysis UUID
            business_profile: Optional business profile (will query if not provided)

        Returns:
            List of NexusResult objects

        Steps:
            1. Get business profile and transactions
            2. Determine physical nexus states
            3. Get all nexus rules
            4. For each state, check economic nexus
            5. Calculate confidence levels
            6. Calculate registration deadlines
            7. Generate recommendations
        """
        logger.info(f"Starting nexus determination for analysis {analysis_id}")

        # Get business profile if not provided
        if business_profile is None:
            business_profile = self.db.query(BusinessProfile).filter(
                BusinessProfile.analysis_id == analysis_id
            ).first()

        # Get analysis for period info
        analysis = self.db.query(Analysis).filter(
            Analysis.analysis_id == analysis_id
        ).first()

        if not analysis:
            raise ValueError(f"Analysis {analysis_id} not found")

        # Determine physical nexus states
        physical_nexus_states = set()
        if business_profile:
            physical_nexus_states = set(
                business_profile_service.get_physical_nexus_states(business_profile)
            )
            logger.info(f"Physical nexus in {len(physical_nexus_states)} states: {physical_nexus_states}")

        # Get all nexus rules for states with sales tax
        nexus_rules = self.db.query(NexusRule).filter(
            NexusRule.nexus_type == 'economic'
        ).all()

        results = []

        # Determine nexus for each state
        for rule in nexus_rules:
            state = rule.state_code

            # Determine if physical nexus exists
            has_physical_nexus = state in physical_nexus_states

            # Calculate economic nexus
            economic_result = self._check_economic_nexus(
                analysis_id,
                state,
                rule,
                analysis.period_end
            )

            # Determine overall nexus status
            if has_physical_nexus:
                nexus_status = NexusStatus.NEXUS_PHYSICAL
                nexus_date = self._determine_physical_nexus_date(
                    business_profile,
                    state
                )
            elif economic_result['has_nexus']:
                nexus_status = NexusStatus.NEXUS_ECONOMIC
                nexus_date = economic_result['nexus_date']
            elif economic_result['close_to_threshold']:
                nexus_status = NexusStatus.CLOSE_TO_THRESHOLD
                nexus_date = None
            else:
                nexus_status = NexusStatus.NO_NEXUS
                nexus_date = None

            # Calculate confidence level
            confidence = self._calculate_confidence_level(
                has_physical_nexus,
                economic_result,
                business_profile
            )

            # Calculate registration deadline
            registration_deadline = None
            if nexus_date and nexus_status in [NexusStatus.NEXUS_PHYSICAL, NexusStatus.NEXUS_ECONOMIC]:
                registration_deadline = self._calculate_registration_deadline(
                    nexus_date,
                    rule.registration_threshold_days or 60
                )

            # Generate recommendation
            recommendation = self._generate_recommendation(
                nexus_status,
                has_physical_nexus,
                economic_result,
                registration_deadline
            )

            # Create nexus result
            result = NexusResult(
                analysis_id=analysis_id,
                state=state,
                nexus_status=nexus_status,
                nexus_date=nexus_date,
                physical_nexus=has_physical_nexus,
                economic_nexus=economic_result['has_nexus'],
                total_sales=economic_result['total_sales'],
                taxable_sales=economic_result['taxable_sales'],
                transaction_count=economic_result['transaction_count'],
                sales_threshold=rule.sales_threshold,
                transaction_threshold=rule.transaction_threshold,
                threshold_type=rule.threshold_type.value if rule.threshold_type else None,
                measurement_period=rule.measurement_period.value if rule.measurement_period else None,
                confidence_level=confidence,
                registration_deadline=registration_deadline,
                close_to_threshold=economic_result['close_to_threshold'],
                threshold_percentage=economic_result['threshold_percentage'],
                days_until_threshold=economic_result['days_until_threshold'],
                recommendation=recommendation,
                calculation_notes=economic_result['notes']
            )

            results.append(result)
            self.db.add(result)

        # Commit all results
        self.db.commit()

        logger.info(f"Nexus determination complete: {len(results)} states analyzed")
        return results

    def _check_economic_nexus(
        self,
        analysis_id: str,
        state: str,
        rule: NexusRule,
        period_end_date: date
    ) -> Dict:
        """
        Check if economic nexus threshold is met for a state.

        Args:
            analysis_id: Analysis UUID
            state: State code
            rule: Nexus rule for the state
            period_end_date: End date of analysis period

        Returns:
            Dict with nexus determination details
        """
        # Calculate measurement period dates
        period_start, period_end = self._calculate_measurement_period(
            rule.measurement_period,
            period_end_date
        )

        logger.debug(f"Checking economic nexus for {state}: {period_start} to {period_end}")

        # Get transactions for the state in the measurement period
        transactions = self.db.query(Transaction).filter(
            Transaction.analysis_id == analysis_id,
            Transaction.customer_state == state,
            Transaction.transaction_date >= period_start,
            Transaction.transaction_date <= period_end
        ).all()

        # Calculate sales and transaction counts
        total_sales = Decimal('0')
        taxable_sales = Decimal('0')
        transaction_count = 0
        marketplace_sales = Decimal('0')

        for txn in transactions:
            total_sales += txn.gross_amount
            transaction_count += 1

            # Exclude marketplace facilitator sales if applicable
            if txn.is_marketplace_sale and rule.exclude_marketplace_sales:
                marketplace_sales += txn.gross_amount
            else:
                # Exclude exempt sales from taxable calculation
                if not txn.is_exempt_sale:
                    taxable_sales += txn.gross_amount

        # Check if threshold is met based on threshold type
        has_nexus = False
        threshold_met_reason = []
        notes = []

        if rule.threshold_type == ThresholdType.SALES_ONLY:
            if taxable_sales >= rule.sales_threshold:
                has_nexus = True
                threshold_met_reason.append(f"Sales ${taxable_sales:,.2f} >= ${rule.sales_threshold:,.2f}")

        elif rule.threshold_type == ThresholdType.TRANSACTIONS_ONLY:
            if transaction_count >= rule.transaction_threshold:
                has_nexus = True
                threshold_met_reason.append(f"{transaction_count} transactions >= {rule.transaction_threshold}")

        elif rule.threshold_type == ThresholdType.EITHER:
            sales_met = taxable_sales >= rule.sales_threshold
            transactions_met = transaction_count >= rule.transaction_threshold

            if sales_met or transactions_met:
                has_nexus = True
                if sales_met:
                    threshold_met_reason.append(f"Sales ${taxable_sales:,.2f} >= ${rule.sales_threshold:,.2f}")
                if transactions_met:
                    threshold_met_reason.append(f"{transaction_count} transactions >= {rule.transaction_threshold}")

        elif rule.threshold_type == ThresholdType.BOTH:
            sales_met = taxable_sales >= rule.sales_threshold
            transactions_met = transaction_count >= rule.transaction_threshold

            if sales_met and transactions_met:
                has_nexus = True
                threshold_met_reason.append(
                    f"Sales ${taxable_sales:,.2f} >= ${rule.sales_threshold:,.2f} AND "
                    f"{transaction_count} transactions >= {rule.transaction_threshold}"
                )

        # Add notes about excluded sales
        if marketplace_sales > 0:
            notes.append(f"Excluded ${marketplace_sales:,.2f} in marketplace facilitator sales")

        if threshold_met_reason:
            notes.append("; ".join(threshold_met_reason))

        # Determine nexus date if nexus exists
        nexus_date = None
        if has_nexus:
            nexus_date = self._determine_economic_nexus_date(
                analysis_id,
                state,
                rule,
                period_end
            )

        # Check if close to threshold
        close_to_threshold, threshold_percentage, days_until = self._check_close_to_threshold(
            taxable_sales,
            transaction_count,
            rule,
            transactions
        )

        return {
            'has_nexus': has_nexus,
            'nexus_date': nexus_date,
            'total_sales': float(total_sales),
            'taxable_sales': float(taxable_sales),
            'transaction_count': transaction_count,
            'marketplace_sales': float(marketplace_sales),
            'close_to_threshold': close_to_threshold,
            'threshold_percentage': threshold_percentage,
            'days_until_threshold': days_until,
            'notes': "; ".join(notes) if notes else None
        }

    def _calculate_measurement_period(
        self,
        measurement_period: MeasurementPeriod,
        reference_date: date
    ) -> Tuple[date, date]:
        """
        Calculate measurement period start and end dates.

        Args:
            measurement_period: Type of measurement period
            reference_date: Reference date (typically end of analysis period)

        Returns:
            Tuple of (start_date, end_date)
        """
        if measurement_period == MeasurementPeriod.CALENDAR_YEAR:
            # Current calendar year up to reference date
            start_date = date(reference_date.year, 1, 1)
            end_date = reference_date

        elif measurement_period == MeasurementPeriod.PREVIOUS_CALENDAR_YEAR:
            # Previous calendar year
            previous_year = reference_date.year - 1
            start_date = date(previous_year, 1, 1)
            end_date = date(previous_year, 12, 31)

        elif measurement_period == MeasurementPeriod.ROLLING_12_MONTHS:
            # 12 months prior to reference date
            start_date = reference_date - relativedelta(months=12) + relativedelta(days=1)
            end_date = reference_date

        else:
            # Default to rolling 12 months
            start_date = reference_date - relativedelta(months=12) + relativedelta(days=1)
            end_date = reference_date

        return start_date, end_date

    def _determine_economic_nexus_date(
        self,
        analysis_id: str,
        state: str,
        rule: NexusRule,
        period_end: date
    ) -> Optional[date]:
        """
        Determine the date when economic nexus was first established.

        Args:
            analysis_id: Analysis UUID
            state: State code
            rule: Nexus rule
            period_end: End of analysis period

        Returns:
            Date when nexus was first established (or None if cannot determine)
        """
        # Get all transactions for this state, ordered by date
        transactions = self.db.query(Transaction).filter(
            Transaction.analysis_id == analysis_id,
            Transaction.customer_state == state
        ).order_by(Transaction.transaction_date).all()

        if not transactions:
            return None

        # Track running totals
        running_sales = Decimal('0')
        running_transactions = 0

        for txn in transactions:
            # Update totals
            if not txn.is_exempt_sale and not (txn.is_marketplace_sale and rule.exclude_marketplace_sales):
                running_sales += txn.gross_amount
            running_transactions += 1

            # Check if threshold crossed
            threshold_crossed = False

            if rule.threshold_type == ThresholdType.SALES_ONLY:
                if running_sales >= rule.sales_threshold:
                    threshold_crossed = True

            elif rule.threshold_type == ThresholdType.TRANSACTIONS_ONLY:
                if running_transactions >= rule.transaction_threshold:
                    threshold_crossed = True

            elif rule.threshold_type == ThresholdType.EITHER:
                if running_sales >= rule.sales_threshold or running_transactions >= rule.transaction_threshold:
                    threshold_crossed = True

            elif rule.threshold_type == ThresholdType.BOTH:
                if running_sales >= rule.sales_threshold and running_transactions >= rule.transaction_threshold:
                    threshold_crossed = True

            if threshold_crossed:
                logger.debug(f"Economic nexus established in {state} on {txn.transaction_date}")
                return txn.transaction_date

        return None

    def _determine_physical_nexus_date(
        self,
        business_profile: Optional[BusinessProfile],
        state: str
    ) -> Optional[date]:
        """
        Determine the date when physical nexus was established.

        Args:
            business_profile: Business profile
            state: State code

        Returns:
            Date when physical nexus was first established
        """
        if not business_profile or not business_profile.physical_locations:
            return None

        # Find earliest established date for locations in this state
        earliest_date = None

        for location in business_profile.physical_locations:
            if location.state.upper() == state.upper():
                if location.established_date:
                    if earliest_date is None or location.established_date < earliest_date:
                        earliest_date = location.established_date

        return earliest_date

    def _check_close_to_threshold(
        self,
        taxable_sales: Decimal,
        transaction_count: int,
        rule: NexusRule,
        transactions: List[Transaction]
    ) -> Tuple[bool, Optional[float], Optional[int]]:
        """
        Check if sales/transactions are close to nexus threshold.

        Args:
            taxable_sales: Taxable sales amount
            transaction_count: Transaction count
            rule: Nexus rule
            transactions: List of transactions

        Returns:
            Tuple of (is_close, percentage_of_threshold, estimated_days_until_threshold)
        """
        is_close = False
        threshold_percentage = None
        days_until = None

        if rule.threshold_type in [ThresholdType.SALES_ONLY, ThresholdType.EITHER, ThresholdType.BOTH]:
            if rule.sales_threshold:
                sales_percentage = float(taxable_sales / rule.sales_threshold)
                threshold_percentage = sales_percentage * 100

                if sales_percentage >= THRESHOLD_WARNING_PERCENTAGE and sales_percentage < 1.0:
                    is_close = True

                    # Estimate days until threshold
                    days_until = self._estimate_days_until_threshold(
                        float(taxable_sales),
                        float(rule.sales_threshold),
                        transactions
                    )

        if rule.threshold_type in [ThresholdType.TRANSACTIONS_ONLY, ThresholdType.EITHER, ThresholdType.BOTH]:
            if rule.transaction_threshold:
                txn_percentage = transaction_count / rule.transaction_threshold

                if threshold_percentage is None:
                    threshold_percentage = txn_percentage * 100

                if txn_percentage >= THRESHOLD_WARNING_PERCENTAGE and txn_percentage < 1.0:
                    is_close = True

        return is_close, threshold_percentage, days_until

    def _estimate_days_until_threshold(
        self,
        current_sales: float,
        threshold: float,
        transactions: List[Transaction]
    ) -> Optional[int]:
        """
        Estimate days until threshold will be reached.

        Args:
            current_sales: Current sales amount
            threshold: Threshold amount
            transactions: List of transactions (for calculating velocity)

        Returns:
            Estimated days until threshold (or None if cannot estimate)
        """
        if len(transactions) < 2:
            return None

        # Calculate daily average sales rate from recent transactions
        sorted_txns = sorted(transactions, key=lambda t: t.transaction_date)
        recent_txns = sorted_txns[-30:] if len(sorted_txns) >= 30 else sorted_txns  # Last 30 or all

        if len(recent_txns) < 2:
            return None

        date_range = (recent_txns[-1].transaction_date - recent_txns[0].transaction_date).days
        if date_range == 0:
            return None

        total_recent_sales = sum(float(t.gross_amount) for t in recent_txns if not t.is_exempt_sale)
        daily_rate = total_recent_sales / date_range

        if daily_rate <= 0:
            return None

        remaining = threshold - current_sales
        days_estimate = int(remaining / daily_rate)

        return max(0, days_estimate)

    def _calculate_confidence_level(
        self,
        has_physical_nexus: bool,
        economic_result: Dict,
        business_profile: Optional[BusinessProfile]
    ) -> ConfidenceLevel:
        """
        Calculate confidence level for nexus determination.

        Args:
            has_physical_nexus: Whether physical nexus exists
            economic_result: Economic nexus calculation results
            business_profile: Business profile

        Returns:
            ConfidenceLevel enum value
        """
        # High confidence: Clear physical presence or well over economic threshold
        if has_physical_nexus:
            return ConfidenceLevel.HIGH

        if economic_result['has_nexus']:
            # Check how far over threshold
            if economic_result['taxable_sales'] > 0:
                sales_threshold = economic_result.get('sales_threshold', 0)
                if sales_threshold and economic_result['taxable_sales'] >= sales_threshold * 1.5:
                    return ConfidenceLevel.HIGH

            return ConfidenceLevel.MEDIUM

        # Medium confidence: Close to threshold
        if economic_result['close_to_threshold']:
            return ConfidenceLevel.MEDIUM

        # Low confidence: No nexus but limited data
        if economic_result['transaction_count'] < 10:
            return ConfidenceLevel.LOW

        # High confidence: Well below threshold with good data
        return ConfidenceLevel.HIGH

    def _calculate_registration_deadline(
        self,
        nexus_date: date,
        threshold_days: int
    ) -> date:
        """
        Calculate registration deadline based on nexus date.

        Args:
            nexus_date: Date when nexus was established
            threshold_days: Days after nexus to register

        Returns:
            Registration deadline date
        """
        return nexus_date + timedelta(days=threshold_days)

    def _generate_recommendation(
        self,
        nexus_status: NexusStatus,
        has_physical_nexus: bool,
        economic_result: Dict,
        registration_deadline: Optional[date]
    ) -> str:
        """
        Generate recommendation text based on nexus determination.

        Args:
            nexus_status: Nexus status
            has_physical_nexus: Whether physical nexus exists
            economic_result: Economic nexus results
            registration_deadline: Registration deadline

        Returns:
            Recommendation string
        """
        if nexus_status == NexusStatus.NEXUS_PHYSICAL:
            if registration_deadline and registration_deadline < date.today():
                return "URGENT: Physical nexus established. Registration deadline has passed. Consult tax advisor immediately."
            elif registration_deadline:
                return f"Physical nexus established. Register for sales tax permit by {registration_deadline.strftime('%Y-%m-%d')}."
            else:
                return "Physical nexus established. Register for sales tax permit as soon as possible."

        elif nexus_status == NexusStatus.NEXUS_ECONOMIC:
            if registration_deadline and registration_deadline < date.today():
                return "URGENT: Economic nexus threshold exceeded. Registration deadline has passed. Consult tax advisor immediately."
            elif registration_deadline:
                return f"Economic nexus threshold exceeded. Register by {registration_deadline.strftime('%Y-%m-%d')}."
            else:
                return "Economic nexus threshold exceeded. Register for sales tax permit."

        elif nexus_status == NexusStatus.CLOSE_TO_THRESHOLD:
            threshold_pct = economic_result.get('threshold_percentage', 0)
            days_until = economic_result.get('days_until_threshold')

            rec = f"Approaching threshold ({threshold_pct:.0f}% of threshold). Monitor sales closely."
            if days_until:
                rec += f" Estimated {days_until} days until threshold reached."
            return rec

        else:
            return "No nexus obligation at this time. Continue monitoring sales activity."


# Create global instance factory
def create_nexus_engine(db: Session) -> NexusEngine:
    """Create nexus engine instance with database session."""
    return NexusEngine(db)

"""
Report generation service for PDF reports.
"""

from sqlalchemy.orm import Session
from typing import Dict, Optional, List
from datetime import datetime, date
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML, CSS
import io
import os
import logging

from models.analysis import Analysis
from models.nexus_result import NexusResult, NexusStatus
from models.liability_estimate import LiabilityEstimate, RiskLevel
from models.business_profile import BusinessProfile
from models.transaction import Transaction
from models.report import Report, ReportType
from models.tenant import Tenant
from services.s3_service import s3_service

logger = logging.getLogger(__name__)

# Template directory
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates', 'reports')


class ReportGenerator:
    """Service for generating PDF reports."""

    def __init__(self, db: Session):
        """
        Initialize report generator.

        Args:
            db: Database session
        """
        self.db = db

        # Set up Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(TEMPLATE_DIR),
            autoescape=select_autoescape(['html', 'xml'])
        )

        # Register custom filters
        self.jinja_env.filters['currency'] = self._format_currency
        self.jinja_env.filters['percent'] = self._format_percent
        self.jinja_env.filters['date'] = self._format_date

    def generate_summary_report(
        self,
        analysis_id: str,
        include_branding: bool = True
    ) -> str:
        """
        Generate executive summary report.

        Args:
            analysis_id: Analysis UUID
            include_branding: Whether to include tenant branding

        Returns:
            Report UUID
        """
        logger.info(f"Generating summary report for analysis {analysis_id}")

        # Fetch all data
        data = self._fetch_analysis_data(analysis_id, include_branding)

        # Generate HTML
        template = self.jinja_env.get_template('summary_report.html')
        html_content = template.render(**data)

        # Generate PDF
        pdf_bytes = self._generate_pdf(html_content, data.get('tenant_colors'))

        # Store in S3
        report_path = self._store_pdf(
            analysis_id,
            data['tenant']['tenant_id'],
            pdf_bytes,
            'summary_report.pdf'
        )

        # Create report record
        report = Report(
            analysis_id=analysis_id,
            report_type=ReportType.EXECUTIVE_SUMMARY,
            file_path=report_path,
            file_size=len(pdf_bytes)
        )

        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)

        logger.info(f"Summary report generated: {report.report_id}")
        return str(report.report_id)

    def generate_detailed_report(
        self,
        analysis_id: str,
        include_branding: bool = True
    ) -> str:
        """
        Generate detailed analysis report.

        Args:
            analysis_id: Analysis UUID
            include_branding: Whether to include tenant branding

        Returns:
            Report UUID
        """
        logger.info(f"Generating detailed report for analysis {analysis_id}")

        # Fetch all data
        data = self._fetch_analysis_data(analysis_id, include_branding)

        # Add detailed sections
        data['include_methodology'] = True
        data['include_state_details'] = True

        # Generate HTML
        template = self.jinja_env.get_template('detailed_report.html')
        html_content = template.render(**data)

        # Generate PDF
        pdf_bytes = self._generate_pdf(html_content, data.get('tenant_colors'))

        # Store in S3
        report_path = self._store_pdf(
            analysis_id,
            data['tenant']['tenant_id'],
            pdf_bytes,
            'detailed_report.pdf'
        )

        # Create report record
        report = Report(
            analysis_id=analysis_id,
            report_type=ReportType.DETAILED_ANALYSIS,
            file_path=report_path,
            file_size=len(pdf_bytes)
        )

        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)

        logger.info(f"Detailed report generated: {report.report_id}")
        return str(report.report_id)

    def _fetch_analysis_data(
        self,
        analysis_id: str,
        include_branding: bool = True
    ) -> Dict:
        """
        Fetch and format all data needed for reports.

        Args:
            analysis_id: Analysis UUID
            include_branding: Whether to include tenant branding

        Returns:
            Dict with all report data
        """
        # Get analysis
        analysis = self.db.query(Analysis).filter(
            Analysis.analysis_id == analysis_id
        ).first()

        if not analysis:
            raise ValueError(f"Analysis {analysis_id} not found")

        # Get tenant
        tenant = self.db.query(Tenant).filter(
            Tenant.tenant_id == analysis.tenant_id
        ).first()

        # Get business profile
        business_profile = self.db.query(BusinessProfile).filter(
            BusinessProfile.analysis_id == analysis_id
        ).first()

        # Get nexus results
        nexus_results = self.db.query(NexusResult).filter(
            NexusResult.analysis_id == analysis_id
        ).order_by(NexusResult.state).all()

        # Get liability estimates
        liability_estimates = self.db.query(LiabilityEstimate).filter(
            LiabilityEstimate.analysis_id == analysis_id
        ).order_by(LiabilityEstimate.estimated_liability_mid.desc()).all()

        # Get transaction summary
        transaction_summary = self._calculate_transaction_summary(analysis_id)

        # Format nexus summary
        nexus_summary = self._format_nexus_summary(nexus_results)

        # Format liability summary
        liability_summary = self._format_liability_summary(liability_estimates)

        # Format recommendations
        recommendations = self._generate_recommendations(
            nexus_results,
            liability_estimates
        )

        # Build data dict
        data = {
            'analysis': {
                'analysis_id': str(analysis.analysis_id),
                'client_name': analysis.client_name,
                'period_start': analysis.period_start,
                'period_end': analysis.period_end,
                'created_at': analysis.created_at,
                'completed_at': analysis.completed_at
            },
            'tenant': {
                'tenant_id': str(tenant.tenant_id),
                'company_name': tenant.company_name,
                'logo_url': tenant.logo_url if include_branding else None
            },
            'tenant_colors': {
                'primary': tenant.primary_color if include_branding else '#1e40af',
                'secondary': tenant.secondary_color if include_branding else '#3b82f6'
            } if include_branding else None,
            'business_profile': self._format_business_profile(business_profile) if business_profile else None,
            'transaction_summary': transaction_summary,
            'nexus_summary': nexus_summary,
            'nexus_results': [self._format_nexus_result(nr) for nr in nexus_results],
            'liability_summary': liability_summary,
            'liability_estimates': [self._format_liability_estimate(le) for le in liability_estimates],
            'recommendations': recommendations,
            'generated_at': datetime.now(),
            'methodology': self._get_methodology_text(),
            'disclaimers': self._get_disclaimers_text()
        }

        return data

    def _calculate_transaction_summary(self, analysis_id: str) -> Dict:
        """Calculate transaction summary statistics."""
        transactions = self.db.query(Transaction).filter(
            Transaction.analysis_id == analysis_id
        ).all()

        total_transactions = len(transactions)
        total_sales = sum(t.gross_amount for t in transactions)
        unique_states = len(set(t.customer_state for t in transactions))
        marketplace_transactions = sum(1 for t in transactions if t.is_marketplace_sale)
        exempt_transactions = sum(1 for t in transactions if t.is_exempt_sale)

        return {
            'total_transactions': total_transactions,
            'total_sales': float(total_sales),
            'unique_states': unique_states,
            'marketplace_transactions': marketplace_transactions,
            'exempt_transactions': exempt_transactions,
            'avg_transaction_value': float(total_sales / total_transactions) if total_transactions > 0 else 0
        }

    def _format_nexus_summary(self, nexus_results: List[NexusResult]) -> Dict:
        """Format nexus results summary."""
        physical_nexus = [nr for nr in nexus_results if nr.nexus_status == NexusStatus.NEXUS_PHYSICAL]
        economic_nexus = [nr for nr in nexus_results if nr.nexus_status == NexusStatus.NEXUS_ECONOMIC]
        close_to_threshold = [nr for nr in nexus_results if nr.nexus_status == NexusStatus.CLOSE_TO_THRESHOLD]
        no_nexus = [nr for nr in nexus_results if nr.nexus_status == NexusStatus.NO_NEXUS]

        return {
            'total_states_analyzed': len(nexus_results),
            'physical_nexus_count': len(physical_nexus),
            'economic_nexus_count': len(economic_nexus),
            'total_nexus_states': len(physical_nexus) + len(economic_nexus),
            'close_to_threshold_count': len(close_to_threshold),
            'no_nexus_count': len(no_nexus),
            'physical_nexus_states': [nr.state for nr in physical_nexus],
            'economic_nexus_states': [nr.state for nr in economic_nexus],
            'close_to_threshold_states': [nr.state for nr in close_to_threshold]
        }

    def _format_liability_summary(self, liability_estimates: List[LiabilityEstimate]) -> Dict:
        """Format liability estimates summary."""
        if not liability_estimates:
            return {
                'total_liability_low': 0,
                'total_liability_mid': 0,
                'total_liability_high': 0,
                'total_lookback_liability': 0,
                'total_penalties': 0,
                'total_interest': 0,
                'high_risk_count': 0,
                'medium_risk_count': 0,
                'low_risk_count': 0
            }

        high_risk = [le for le in liability_estimates if le.risk_level == RiskLevel.HIGH]
        medium_risk = [le for le in liability_estimates if le.risk_level == RiskLevel.MEDIUM]
        low_risk = [le for le in liability_estimates if le.risk_level == RiskLevel.LOW]

        return {
            'total_liability_low': sum(le.estimated_liability_low or 0 for le in liability_estimates),
            'total_liability_mid': sum(le.estimated_liability_mid or 0 for le in liability_estimates),
            'total_liability_high': sum(le.estimated_liability_high or 0 for le in liability_estimates),
            'total_lookback_liability': sum(le.lookback_liability_estimate or 0 for le in liability_estimates),
            'total_penalties': sum(le.penalty_amount or 0 for le in liability_estimates),
            'total_interest': sum(le.interest_amount or 0 for le in liability_estimates),
            'high_risk_count': len(high_risk),
            'medium_risk_count': len(medium_risk),
            'low_risk_count': len(low_risk),
            'high_risk_states': [le.state for le in high_risk],
            'top_5_states': [
                {'state': le.state, 'liability': le.estimated_liability_mid}
                for le in liability_estimates[:5]
            ]
        }

    def _format_business_profile(self, profile: BusinessProfile) -> Dict:
        """Format business profile data."""
        return {
            'legal_business_name': profile.legal_business_name,
            'doing_business_as': profile.doing_business_as,
            'business_structure': profile.business_structure,
            'has_physical_presence': profile.has_physical_presence,
            'has_employees': profile.has_employees,
            'location_count': len(profile.physical_locations) if profile.physical_locations else 0,
            'uses_marketplace_facilitators': profile.uses_marketplace_facilitators,
            'marketplace_names': profile.marketplace_facilitator_names or []
        }

    def _format_nexus_result(self, result: NexusResult) -> Dict:
        """Format individual nexus result."""
        return {
            'state': result.state,
            'nexus_status': result.nexus_status.value,
            'nexus_status_label': result.nexus_status.value.replace('_', ' ').title(),
            'physical_nexus': result.physical_nexus,
            'economic_nexus': result.economic_nexus,
            'total_sales': result.total_sales,
            'taxable_sales': result.taxable_sales,
            'transaction_count': result.transaction_count,
            'confidence_level': result.confidence_level.value if result.confidence_level else None,
            'registration_deadline': result.registration_deadline,
            'recommendation': result.recommendation
        }

    def _format_liability_estimate(self, estimate: LiabilityEstimate) -> Dict:
        """Format individual liability estimate."""
        return {
            'state': estimate.state,
            'taxable_sales': estimate.taxable_sales,
            'estimated_liability_low': estimate.estimated_liability_low,
            'estimated_liability_mid': estimate.estimated_liability_mid,
            'estimated_liability_high': estimate.estimated_liability_high,
            'lookback_liability': estimate.lookback_liability_estimate,
            'penalty_amount': estimate.penalty_amount,
            'interest_amount': estimate.interest_amount,
            'total_with_penalties': estimate.total_liability_with_penalties,
            'risk_level': estimate.risk_level.value if estimate.risk_level else None,
            'recommendation': estimate.recommendation
        }

    def _generate_recommendations(
        self,
        nexus_results: List[NexusResult],
        liability_estimates: List[LiabilityEstimate]
    ) -> List[Dict]:
        """Generate prioritized recommendations."""
        recommendations = []

        # High priority: States with penalties
        states_with_penalties = [
            le for le in liability_estimates
            if le.penalty_amount and le.penalty_amount > 0
        ]

        if states_with_penalties:
            recommendations.append({
                'priority': 'URGENT',
                'category': 'Penalties Accruing',
                'description': f"{len(states_with_penalties)} states have passed registration deadlines",
                'action': "Consider Voluntary Disclosure Agreements (VDA) to minimize penalties",
                'states': [le.state for le in states_with_penalties]
            })

        # High priority: High risk states
        high_risk_states = [
            le for le in liability_estimates
            if le.risk_level == RiskLevel.HIGH
        ]

        if high_risk_states:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'High Risk States',
                'description': f"{len(high_risk_states)} states identified as high risk",
                'action': "Consult with tax professional immediately for compliance strategy",
                'states': [le.state for le in high_risk_states]
            })

        # Medium priority: Large liability states
        large_liability_states = [
            le for le in liability_estimates
            if le.estimated_liability_mid and le.estimated_liability_mid > 10000
        ]

        if large_liability_states:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'Significant Liability',
                'description': f"{len(large_liability_states)} states with liability > $10,000",
                'action': "Prioritize these states for registration and filing",
                'states': [le.state for le in large_liability_states[:5]]  # Top 5
            })

        # Medium priority: Close to threshold
        close_states = [
            nr for nr in nexus_results
            if nr.nexus_status == NexusStatus.CLOSE_TO_THRESHOLD
        ]

        if close_states:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'Approaching Threshold',
                'description': f"{len(close_states)} states close to nexus threshold",
                'action': "Monitor sales in these states closely",
                'states': [nr.state for nr in close_states]
            })

        # General recommendation
        recommendations.append({
            'priority': 'GENERAL',
            'category': 'Compliance Program',
            'description': "Establish ongoing nexus monitoring and compliance procedures",
            'action': "Implement quarterly nexus reviews and sales tax collection processes",
            'states': []
        })

        return recommendations

    def _get_methodology_text(self) -> str:
        """Get methodology explanation text."""
        return """
This analysis uses the following methodology:

1. **Physical Nexus**: Determined by documented physical locations including offices,
   warehouses, retail stores, and remote employee locations.

2. **Economic Nexus**: Calculated based on current state thresholds (typically $100,000
   in sales OR 200 transactions). Measurement periods vary by state (calendar year,
   previous year, or rolling 12 months).

3. **Liability Estimation**:
   - Low Estimate: State tax rate only
   - Mid Estimate: State rate + 50% of average local rate
   - High Estimate: State rate + full average local rate
   - Conservative 10% exemption rate assumed for unknown exemptions

4. **Lookback Period**: Typically 3-4 years from nexus establishment date, varies by state.

5. **Penalties & Interest**: 10% penalty plus 1% monthly interest for late registration.

6. **Risk Assessment**: Based on nexus type, liability amount, confidence level, and
   penalty status.
"""

    def _get_disclaimers_text(self) -> str:
        """Get disclaimers text."""
        return """
**IMPORTANT DISCLAIMERS:**

This report is provided for informational purposes only and should not be considered legal
or tax advice. The estimates and recommendations contained herein are based on the information
provided and current state sales tax laws as of the analysis date.

- Actual sales tax liability may differ from estimates
- State laws and thresholds change frequently
- Individual circumstances may create additional obligations or exemptions
- Consult with a qualified sales tax professional before taking action
- This analysis does not constitute a guarantee or warranty

The information in this report is current as of the date generated and may become outdated
as state laws change or additional information becomes available.
"""

    def _generate_pdf(self, html_content: str, tenant_colors: Optional[Dict] = None) -> bytes:
        """
        Generate PDF from HTML content.

        Args:
            html_content: HTML content
            tenant_colors: Optional tenant brand colors

        Returns:
            PDF bytes
        """
        # Apply custom CSS for tenant branding if provided
        css_content = self._generate_css(tenant_colors)

        # Generate PDF
        html = HTML(string=html_content)
        pdf_bytes = html.write_pdf(
            stylesheets=[CSS(string=css_content)] if css_content else None
        )

        return pdf_bytes

    def _generate_css(self, tenant_colors: Optional[Dict] = None) -> str:
        """Generate CSS with optional tenant branding."""
        if not tenant_colors:
            return ""

        return f"""
        :root {{
            --primary-color: {tenant_colors.get('primary', '#1e40af')};
            --secondary-color: {tenant_colors.get('secondary', '#3b82f6')};
        }}

        h1, h2 {{
            color: var(--primary-color);
        }}

        .header {{
            background-color: var(--primary-color);
        }}

        .accent {{
            color: var(--secondary-color);
        }}
        """

    def _store_pdf(
        self,
        analysis_id: str,
        tenant_id: str,
        pdf_bytes: bytes,
        filename: str
    ) -> str:
        """
        Store PDF in S3.

        Args:
            analysis_id: Analysis UUID
            tenant_id: Tenant UUID
            pdf_bytes: PDF content
            filename: Filename

        Returns:
            S3 object key
        """
        object_key = s3_service.build_object_key(
            str(tenant_id),
            str(analysis_id),
            f"reports/{filename}"
        )

        s3_service.upload_file(
            io.BytesIO(pdf_bytes),
            object_key,
            'application/pdf'
        )

        return object_key

    def _format_currency(self, value: Optional[float]) -> str:
        """Format currency for templates."""
        if value is None:
            return "$0.00"
        return f"${value:,.2f}"

    def _format_percent(self, value: Optional[float]) -> str:
        """Format percentage for templates."""
        if value is None:
            return "0.0%"
        return f"{value:.1f}%"

    def _format_date(self, value: Optional[date]) -> str:
        """Format date for templates."""
        if value is None:
            return "N/A"
        return value.strftime("%B %d, %Y")


# Create global instance factory
def create_report_generator(db: Session) -> ReportGenerator:
    """Create report generator instance with database session."""
    return ReportGenerator(db)

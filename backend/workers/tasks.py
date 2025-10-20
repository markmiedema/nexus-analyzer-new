"""
Celery background tasks for Nexus Analyzer.
"""

from workers.celery_app import celery_app
from database import SessionLocal
from models.analysis import Analysis, AnalysisStatus
from services.csv_processor import csv_processor
from services.s3_service import s3_service
import logging
import json
import io

logger = logging.getLogger(__name__)


@celery_app.task(name="workers.tasks.process_csv_file", bind=True, max_retries=3)
def process_csv_file(self, analysis_id: str, csv_file_path: str):
    """
    Process CSV file asynchronously.

    Args:
        analysis_id: Analysis UUID
        csv_file_path: S3 path to CSV file

    Returns:
        dict: Processing results
    """
    db = SessionLocal()

    try:
        # Get analysis
        analysis = db.query(Analysis).filter(
            Analysis.analysis_id == analysis_id
        ).first()

        if not analysis:
            logger.error(f"Analysis {analysis_id} not found")
            return {'success': False, 'error': 'Analysis not found'}

        # Update status
        analysis.status = AnalysisStatus.PROCESSING_CSV
        db.commit()

        # Download CSV from S3
        logger.info(f"Downloading CSV from {csv_file_path}")
        file_content = s3_service.download_file(csv_file_path)

        # Parse CSV
        logger.info(f"Parsing CSV for analysis {analysis_id}")
        df = csv_processor.parse_csv(file_content)

        # Process and validate
        logger.info(f"Processing {len(df)} rows")
        result = csv_processor.process_dataframe(df, analysis_id, db)

        if result['success']:
            # Update analysis status
            analysis.status = AnalysisStatus.PROCESSING_NEXUS
            db.commit()

            logger.info(f"CSV processing complete: {result['valid_rows']} valid rows")

            # Generate validation report if there are errors
            if result['validation_errors']:
                report_content = generate_validation_report(result)
                report_path = s3_service.build_object_key(
                    str(analysis.tenant_id),
                    str(analysis_id),
                    'validation_report.json'
                )
                s3_service.upload_file(
                    io.BytesIO(report_content.encode('utf-8')),
                    report_path,
                    'application/json'
                )
                analysis.validation_report_path = report_path
                db.commit()

            return result
        else:
            # Processing failed
            analysis.status = AnalysisStatus.FAILED
            analysis.error_message = result.get('error', 'CSV processing failed')
            db.commit()

            logger.error(f"CSV processing failed: {result.get('error')}")
            return result

    except Exception as e:
        logger.error(f"Error processing CSV: {e}", exc_info=True)

        # Update analysis status
        try:
            analysis = db.query(Analysis).filter(
                Analysis.analysis_id == analysis_id
            ).first()
            if analysis:
                analysis.status = AnalysisStatus.FAILED
                analysis.error_message = f"Processing error: {str(e)}"
                db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update analysis status: {db_error}")

        # Retry task
        raise self.retry(exc=e, countdown=60)

    finally:
        db.close()


def generate_validation_report(result: dict) -> str:
    """
    Generate validation report JSON.

    Args:
        result: Processing result dictionary

    Returns:
        str: JSON report
    """
    report = {
        'summary': {
            'total_rows': result['total_rows'],
            'valid_rows': result['valid_rows'],
            'invalid_rows': result['invalid_rows'],
            'quality_percentage': result['quality_percentage']
        },
        'validation_errors': result['validation_errors']
    }

    return json.dumps(report, indent=2, default=str)


@celery_app.task(name="workers.tasks.run_nexus_determination", bind=True, max_retries=3)
def run_nexus_determination(self, analysis_id: str):
    """
    Run nexus determination for an analysis.

    Args:
        analysis_id: Analysis UUID

    Returns:
        dict: Nexus determination results summary
    """
    db = SessionLocal()

    try:
        # Get analysis
        analysis = db.query(Analysis).filter(
            Analysis.analysis_id == analysis_id
        ).first()

        if not analysis:
            logger.error(f"Analysis {analysis_id} not found")
            return {'success': False, 'error': 'Analysis not found'}

        # Update status
        analysis.status = AnalysisStatus.PROCESSING_NEXUS
        db.commit()

        # Get business profile
        from models.business_profile import BusinessProfile
        business_profile = db.query(BusinessProfile).filter(
            BusinessProfile.analysis_id == analysis_id
        ).first()

        # Run nexus determination
        logger.info(f"Running nexus determination for analysis {analysis_id}")
        from services.nexus_engine import create_nexus_engine

        engine = create_nexus_engine(db)
        results = engine.determine_nexus(analysis_id, business_profile)

        # Count results by nexus status
        from models.nexus_result import NexusStatus
        nexus_states = sum(1 for r in results if r.nexus_status in [
            NexusStatus.NEXUS_PHYSICAL,
            NexusStatus.NEXUS_ECONOMIC
        ])
        close_states = sum(1 for r in results if r.nexus_status == NexusStatus.CLOSE_TO_THRESHOLD)

        # Update analysis status
        analysis.status = AnalysisStatus.COMPLETED
        analysis.completed_at = func.now()
        db.commit()

        logger.info(
            f"Nexus determination complete: {nexus_states} states with nexus, "
            f"{close_states} states close to threshold"
        )

        return {
            'success': True,
            'states_analyzed': len(results),
            'nexus_states': nexus_states,
            'close_to_threshold': close_states,
            'analysis_id': analysis_id
        }

    except Exception as e:
        logger.error(f"Error running nexus determination: {e}", exc_info=True)

        # Update analysis status
        try:
            analysis = db.query(Analysis).filter(
                Analysis.analysis_id == analysis_id
            ).first()
            if analysis:
                analysis.status = AnalysisStatus.FAILED
                analysis.error_message = f"Nexus determination error: {str(e)}"
                db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update analysis status: {db_error}")

        # Retry task
        raise self.retry(exc=e, countdown=60)

    finally:
        db.close()


@celery_app.task(name="workers.tasks.calculate_liability", bind=True, max_retries=3)
def calculate_liability(
    self,
    analysis_id: str,
    exemption_rate: float = None,
    include_penalties: bool = True,
    custom_lookback_months: int = None
):
    """
    Calculate liability estimates for an analysis.

    Args:
        analysis_id: Analysis UUID
        exemption_rate: Custom exemption rate (optional)
        include_penalties: Whether to include penalty estimates
        custom_lookback_months: Custom lookback period in months

    Returns:
        dict: Liability calculation results summary
    """
    db = SessionLocal()

    try:
        # Get analysis
        analysis = db.query(Analysis).filter(
            Analysis.analysis_id == analysis_id
        ).first()

        if not analysis:
            logger.error(f"Analysis {analysis_id} not found")
            return {'success': False, 'error': 'Analysis not found'}

        # Run liability calculation
        logger.info(f"Running liability calculation for analysis {analysis_id}")
        from services.liability_engine import create_liability_engine

        engine = create_liability_engine(db)
        estimates = engine.calculate_liability(
            analysis_id,
            exemption_rate=exemption_rate,
            include_penalties=include_penalties,
            custom_lookback_months=custom_lookback_months
        )

        # Calculate summary statistics
        from models.liability_estimate import RiskLevel
        total_liability = sum(est.estimated_liability_mid for est in estimates)
        high_risk_states = sum(1 for est in estimates if est.risk_level == RiskLevel.HIGH)
        states_with_penalties = sum(1 for est in estimates if est.penalty_amount and est.penalty_amount > 0)

        logger.info(
            f"Liability calculation complete: {len(estimates)} states, "
            f"${total_liability:,.2f} total liability"
        )

        return {
            'success': True,
            'states_calculated': len(estimates),
            'total_liability_estimate': float(total_liability),
            'high_risk_states': high_risk_states,
            'states_with_penalties': states_with_penalties,
            'analysis_id': analysis_id
        }

    except Exception as e:
        logger.error(f"Error calculating liability: {e}", exc_info=True)

        # Retry task
        raise self.retry(exc=e, countdown=60)

    finally:
        db.close()


@celery_app.task(name="workers.tasks.generate_report", bind=True, max_retries=3)
def generate_report(self, analysis_id: str, report_type: str = 'summary', include_branding: bool = True):
    """
    Generate PDF report for an analysis.

    Args:
        analysis_id: Analysis UUID
        report_type: Type of report ('summary' or 'detailed')
        include_branding: Whether to include tenant branding

    Returns:
        dict: Report generation results
    """
    db = SessionLocal()

    try:
        # Get analysis
        analysis = db.query(Analysis).filter(
            Analysis.analysis_id == analysis_id
        ).first()

        if not analysis:
            logger.error(f"Analysis {analysis_id} not found")
            return {'success': False, 'error': 'Analysis not found'}

        # Generate report
        logger.info(f"Generating {report_type} report for analysis {analysis_id}")
        from services.report_generator import create_report_generator

        generator = create_report_generator(db)

        if report_type == 'summary':
            report_id = generator.generate_summary_report(analysis_id, include_branding)
        elif report_type == 'detailed':
            report_id = generator.generate_detailed_report(analysis_id, include_branding)
        else:
            return {'success': False, 'error': f'Invalid report type: {report_type}'}

        logger.info(f"Report generated successfully: {report_id}")

        return {
            'success': True,
            'report_id': report_id,
            'report_type': report_type,
            'analysis_id': analysis_id
        }

    except Exception as e:
        logger.error(f"Error generating report: {e}", exc_info=True)

        # Retry task
        raise self.retry(exc=e, countdown=60)

    finally:
        db.close()


@celery_app.task(name="workers.tasks.example_task")
def example_task(x: int, y: int) -> int:
    """
    Example Celery task - add two numbers.
    This is a placeholder that will be replaced with actual tasks.
    """
    return x + y

"""
Seed data for nexus_rules table.
Economic nexus thresholds current as of October 2025.
"""

from sqlalchemy.orm import Session
from models.nexus_rule import NexusRule, ThresholdMeasurement, MeasurementPeriod
from database import SessionLocal
import logging
from datetime import date

logger = logging.getLogger(__name__)


NEXUS_RULES_DATA = [
    {
        'state_code': 'AL',
        'nexus_type': 'economic',
        'sales_threshold': 250000.00,
        'transaction_threshold': None,
        'threshold_type': ThresholdMeasurement.SALES_ONLY,
        'measurement_period': MeasurementPeriod.PREVIOUS_CALENDAR_YEAR,
        'effective_date': date(2018, 10, 1),
        'description': 'Alabama economic nexus: $250,000 in sales',
        'registration_threshold_days': 30
    },
    {
        'state_code': 'AK',
        'nexus_type': 'economic',
        'sales_threshold': 100000.00,
        'transaction_threshold': 200,
        'threshold_type': ThresholdMeasurement.EITHER,
        'measurement_period': MeasurementPeriod.CALENDAR_YEAR,
        'effective_date': date(2020, 4, 1),
        'description': 'Alaska remote seller sales tax: $100k OR 200 transactions',
        'registration_threshold_days': 30
    },
    {
        'state_code': 'AZ',
        'nexus_type': 'economic',
        'sales_threshold': 100000.00,
        'transaction_threshold': None,
        'threshold_type': ThresholdMeasurement.SALES_ONLY,
        'measurement_period': MeasurementPeriod.CALENDAR_YEAR,
        'effective_date': date(2019, 10, 1),
        'description': 'Arizona economic nexus: $100,000 in sales',
        'registration_threshold_days': 60
    },
    {
        'state_code': 'AR',
        'nexus_type': 'economic',
        'sales_threshold': 100000.00,
        'transaction_threshold': 200,
        'threshold_type': ThresholdMeasurement.EITHER,
        'measurement_period': MeasurementPeriod.CALENDAR_YEAR,
        'effective_date': date(2019, 7, 1),
        'description': 'Arkansas economic nexus: $100k OR 200 transactions',
        'registration_threshold_days': 60
    },
    {
        'state_code': 'CA',
        'nexus_type': 'economic',
        'sales_threshold': 500000.00,
        'transaction_threshold': None,
        'threshold_type': ThresholdMeasurement.SALES_ONLY,
        'measurement_period': MeasurementPeriod.PREVIOUS_CALENDAR_YEAR,
        'effective_date': date(2019, 4, 1),
        'description': 'California economic nexus: $500,000 in sales',
        'registration_threshold_days': 90
    },
    {
        'state_code': 'CO',
        'nexus_type': 'economic',
        'sales_threshold': 100000.00,
        'transaction_threshold': None,
        'threshold_type': ThresholdMeasurement.SALES_ONLY,
        'measurement_period': MeasurementPeriod.PREVIOUS_CALENDAR_YEAR,
        'effective_date': date(2019, 6, 1),
        'description': 'Colorado economic nexus: $100,000 in sales',
        'registration_threshold_days': 30
    },
    {
        'state_code': 'CT',
        'nexus_type': 'economic',
        'sales_threshold': 100000.00,
        'transaction_threshold': 200,
        'threshold_type': ThresholdMeasurement.BOTH,
        'measurement_period': MeasurementPeriod.ROLLING_12_MONTHS,
        'effective_date': date(2019, 7, 1),
        'description': 'Connecticut economic nexus: $100k AND 200 transactions',
        'registration_threshold_days': 60
    },
    {
        'state_code': 'FL',
        'nexus_type': 'economic',
        'sales_threshold': 100000.00,
        'transaction_threshold': None,
        'threshold_type': ThresholdMeasurement.SALES_ONLY,
        'measurement_period': MeasurementPeriod.PREVIOUS_CALENDAR_YEAR,
        'effective_date': date(2021, 7, 1),
        'description': 'Florida economic nexus: $100,000 in sales',
        'registration_threshold_days': 30
    },
    {
        'state_code': 'GA',
        'nexus_type': 'economic',
        'sales_threshold': 100000.00,
        'transaction_threshold': 200,
        'threshold_type': ThresholdMeasurement.EITHER,
        'measurement_period': MeasurementPeriod.PREVIOUS_CALENDAR_YEAR,
        'effective_date': date(2020, 1, 1),
        'description': 'Georgia economic nexus: $100k OR 200 transactions',
        'registration_threshold_days': 60
    },
    {
        'state_code': 'HI',
        'nexus_type': 'economic',
        'sales_threshold': 100000.00,
        'transaction_threshold': 200,
        'threshold_type': ThresholdMeasurement.EITHER,
        'measurement_period': MeasurementPeriod.CALENDAR_YEAR,
        'effective_date': date(2020, 7, 1),
        'description': 'Hawaii economic nexus: $100k OR 200 transactions',
        'registration_threshold_days': 30
    },
    {
        'state_code': 'ID',
        'nexus_type': 'economic',
        'sales_threshold': 100000.00,
        'transaction_threshold': None,
        'threshold_type': ThresholdMeasurement.SALES_ONLY,
        'measurement_period': MeasurementPeriod.CALENDAR_YEAR,
        'effective_date': date(2019, 6, 1),
        'description': 'Idaho economic nexus: $100,000 in sales',
        'registration_threshold_days': 60
    },
    {
        'state_code': 'IL',
        'nexus_type': 'economic',
        'sales_threshold': 100000.00,
        'transaction_threshold': 200,
        'threshold_type': ThresholdMeasurement.EITHER,
        'measurement_period': MeasurementPeriod.ROLLING_12_MONTHS,
        'effective_date': date(2019, 10, 1),
        'description': 'Illinois economic nexus: $100k OR 200 transactions',
        'registration_threshold_days': 90
    },
    {
        'state_code': 'IN',
        'nexus_type': 'economic',
        'sales_threshold': 100000.00,
        'transaction_threshold': 200,
        'threshold_type': ThresholdMeasurement.EITHER,
        'measurement_period': MeasurementPeriod.CALENDAR_YEAR,
        'effective_date': date(2019, 10, 1),
        'description': 'Indiana economic nexus: $100k OR 200 transactions',
        'registration_threshold_days': 60
    },
    {
        'state_code': 'IA',
        'nexus_type': 'economic',
        'sales_threshold': 100000.00,
        'transaction_threshold': None,
        'threshold_type': ThresholdMeasurement.SALES_ONLY,
        'measurement_period': MeasurementPeriod.PREVIOUS_CALENDAR_YEAR,
        'effective_date': date(2019, 1, 1),
        'description': 'Iowa economic nexus: $100,000 in sales',
        'registration_threshold_days': 60
    },
    {
        'state_code': 'KS',
        'nexus_type': 'economic',
        'sales_threshold': 100000.00,
        'transaction_threshold': None,
        'threshold_type': ThresholdMeasurement.SALES_ONLY,
        'measurement_period': MeasurementPeriod.CALENDAR_YEAR,
        'effective_date': date(2021, 7, 1),
        'description': 'Kansas economic nexus: $100,000 in sales',
        'registration_threshold_days': 30
    },
    {
        'state_code': 'KY',
        'nexus_type': 'economic',
        'sales_threshold': 100000.00,
        'transaction_threshold': 200,
        'threshold_type': ThresholdMeasurement.EITHER,
        'measurement_period': MeasurementPeriod.PREVIOUS_CALENDAR_YEAR,
        'effective_date': date(2019, 7, 1),
        'description': 'Kentucky economic nexus: $100k OR 200 transactions',
        'registration_threshold_days': 60
    },
    {
        'state_code': 'LA',
        'nexus_type': 'economic',
        'sales_threshold': 100000.00,
        'transaction_threshold': 200,
        'threshold_type': ThresholdMeasurement.EITHER,
        'measurement_period': MeasurementPeriod.CALENDAR_YEAR,
        'effective_date': date(2020, 7, 1),
        'description': 'Louisiana economic nexus: $100k OR 200 transactions',
        'registration_threshold_days': 30
    },
    {
        'state_code': 'ME',
        'nexus_type': 'economic',
        'sales_threshold': 100000.00,
        'transaction_threshold': None,
        'threshold_type': ThresholdMeasurement.SALES_ONLY,
        'measurement_period': MeasurementPeriod.CALENDAR_YEAR,
        'effective_date': date(2019, 7, 1),
        'description': 'Maine economic nexus: $100,000 in sales',
        'registration_threshold_days': 30
    },
    {
        'state_code': 'MD',
        'nexus_type': 'economic',
        'sales_threshold': 100000.00,
        'transaction_threshold': 200,
        'threshold_type': ThresholdMeasurement.EITHER,
        'measurement_period': MeasurementPeriod.PREVIOUS_CALENDAR_YEAR,
        'effective_date': date(2019, 10, 1),
        'description': 'Maryland economic nexus: $100k OR 200 transactions',
        'registration_threshold_days': 60
    },
    {
        'state_code': 'MA',
        'nexus_type': 'economic',
        'sales_threshold': 100000.00,
        'transaction_threshold': None,
        'threshold_type': ThresholdMeasurement.SALES_ONLY,
        'measurement_period': MeasurementPeriod.CALENDAR_YEAR,
        'effective_date': date(2019, 10, 1),
        'description': 'Massachusetts economic nexus: $100,000 in sales',
        'registration_threshold_days': 30
    },
    {
        'state_code': 'MI',
        'nexus_type': 'economic',
        'sales_threshold': 100000.00,
        'transaction_threshold': 200,
        'threshold_type': ThresholdMeasurement.EITHER,
        'measurement_period': MeasurementPeriod.PREVIOUS_CALENDAR_YEAR,
        'effective_date': date(2019, 10, 1),
        'description': 'Michigan economic nexus: $100k OR 200 transactions',
        'registration_threshold_days': 60
    },
    {
        'state_code': 'MN',
        'nexus_type': 'economic',
        'sales_threshold': 100000.00,
        'transaction_threshold': 200,
        'threshold_type': ThresholdMeasurement.EITHER,
        'measurement_period': MeasurementPeriod.ROLLING_12_MONTHS,
        'effective_date': date(2019, 10, 1),
        'description': 'Minnesota economic nexus: $100k OR 200 transactions (rolling)',
        'registration_threshold_days': 60
    },
    {
        'state_code': 'MS',
        'nexus_type': 'economic',
        'sales_threshold': 250000.00,
        'transaction_threshold': None,
        'threshold_type': ThresholdMeasurement.SALES_ONLY,
        'measurement_period': MeasurementPeriod.ROLLING_12_MONTHS,
        'effective_date': date(2020, 1, 1),
        'description': 'Mississippi economic nexus: $250,000 in sales',
        'registration_threshold_days': 30
    },
    {
        'state_code': 'MO',
        'nexus_type': 'economic',
        'sales_threshold': 100000.00,
        'transaction_threshold': None,
        'threshold_type': ThresholdMeasurement.SALES_ONLY,
        'measurement_period': MeasurementPeriod.PREVIOUS_CALENDAR_YEAR,
        'effective_date': date(2023, 1, 1),
        'description': 'Missouri economic nexus: $100,000 in sales',
        'registration_threshold_days': 30
    },
    {
        'state_code': 'NE',
        'nexus_type': 'economic',
        'sales_threshold': 100000.00,
        'transaction_threshold': 200,
        'threshold_type': ThresholdMeasurement.EITHER,
        'measurement_period': MeasurementPeriod.CALENDAR_YEAR,
        'effective_date': date(2019, 4, 1),
        'description': 'Nebraska economic nexus: $100k OR 200 transactions',
        'registration_threshold_days': 60
    },
    {
        'state_code': 'NV',
        'nexus_type': 'economic',
        'sales_threshold': 100000.00,
        'transaction_threshold': 200,
        'threshold_type': ThresholdMeasurement.EITHER,
        'measurement_period': MeasurementPeriod.PREVIOUS_CALENDAR_YEAR,
        'effective_date': date(2019, 10, 1),
        'description': 'Nevada economic nexus: $100k OR 200 transactions',
        'registration_threshold_days': 30
    },
    {
        'state_code': 'NJ',
        'nexus_type': 'economic',
        'sales_threshold': 100000.00,
        'transaction_threshold': 200,
        'threshold_type': ThresholdMeasurement.EITHER,
        'measurement_period': MeasurementPeriod.PREVIOUS_CALENDAR_YEAR,
        'effective_date': date(2018, 11, 1),
        'description': 'New Jersey economic nexus: $100k OR 200 transactions',
        'registration_threshold_days': 30
    },
    {
        'state_code': 'NM',
        'nexus_type': 'economic',
        'sales_threshold': 100000.00,
        'transaction_threshold': None,
        'threshold_type': ThresholdMeasurement.SALES_ONLY,
        'measurement_period': MeasurementPeriod.CALENDAR_YEAR,
        'effective_date': date(2019, 7, 1),
        'description': 'New Mexico economic nexus: $100,000 in sales',
        'registration_threshold_days': 60
    },
    {
        'state_code': 'NY',
        'nexus_type': 'economic',
        'sales_threshold': 500000.00,
        'transaction_threshold': 100,
        'threshold_type': ThresholdMeasurement.BOTH,
        'measurement_period': MeasurementPeriod.PREVIOUS_CALENDAR_YEAR,
        'effective_date': date(2019, 6, 1),
        'description': 'New York economic nexus: $500k AND 100 transactions',
        'registration_threshold_days': 60
    },
    {
        'state_code': 'NC',
        'nexus_type': 'economic',
        'sales_threshold': 100000.00,
        'transaction_threshold': 200,
        'threshold_type': ThresholdMeasurement.EITHER,
        'measurement_period': MeasurementPeriod.PREVIOUS_CALENDAR_YEAR,
        'effective_date': date(2019, 11, 1),
        'description': 'North Carolina economic nexus: $100k OR 200 transactions',
        'registration_threshold_days': 60
    },
    {
        'state_code': 'ND',
        'nexus_type': 'economic',
        'sales_threshold': 100000.00,
        'transaction_threshold': None,
        'threshold_type': ThresholdMeasurement.SALES_ONLY,
        'measurement_period': MeasurementPeriod.CALENDAR_YEAR,
        'effective_date': date(2019, 10, 1),
        'description': 'North Dakota economic nexus: $100,000 in sales',
        'registration_threshold_days': 60
    },
    {
        'state_code': 'OH',
        'nexus_type': 'economic',
        'sales_threshold': 100000.00,
        'transaction_threshold': 200,
        'threshold_type': ThresholdMeasurement.EITHER,
        'measurement_period': MeasurementPeriod.PREVIOUS_CALENDAR_YEAR,
        'effective_date': date(2019, 8, 1),
        'description': 'Ohio economic nexus: $100k OR 200 transactions',
        'registration_threshold_days': 30
    },
    {
        'state_code': 'OK',
        'nexus_type': 'economic',
        'sales_threshold': 100000.00,
        'transaction_threshold': None,
        'threshold_type': ThresholdMeasurement.SALES_ONLY,
        'measurement_period': MeasurementPeriod.CALENDAR_YEAR,
        'effective_date': date(2019, 7, 1),
        'description': 'Oklahoma economic nexus: $100,000 in sales',
        'registration_threshold_days': 60
    },
    {
        'state_code': 'PA',
        'nexus_type': 'economic',
        'sales_threshold': 100000.00,
        'transaction_threshold': None,
        'threshold_type': ThresholdMeasurement.SALES_ONLY,
        'measurement_period': MeasurementPeriod.ROLLING_12_MONTHS,
        'effective_date': date(2019, 7, 1),
        'description': 'Pennsylvania economic nexus: $100,000 in sales',
        'registration_threshold_days': 60
    },
    {
        'state_code': 'RI',
        'nexus_type': 'economic',
        'sales_threshold': 100000.00,
        'transaction_threshold': 200,
        'threshold_type': ThresholdMeasurement.EITHER,
        'measurement_period': MeasurementPeriod.CALENDAR_YEAR,
        'effective_date': date(2019, 7, 1),
        'description': 'Rhode Island economic nexus: $100k OR 200 transactions',
        'registration_threshold_days': 30
    },
    {
        'state_code': 'SC',
        'nexus_type': 'economic',
        'sales_threshold': 100000.00,
        'transaction_threshold': None,
        'threshold_type': ThresholdMeasurement.SALES_ONLY,
        'measurement_period': MeasurementPeriod.PREVIOUS_CALENDAR_YEAR,
        'effective_date': date(2019, 4, 26),
        'description': 'South Carolina economic nexus: $100,000 in sales',
        'registration_threshold_days': 60
    },
    {
        'state_code': 'SD',
        'nexus_type': 'economic',
        'sales_threshold': 100000.00,
        'transaction_threshold': 200,
        'threshold_type': ThresholdMeasurement.EITHER,
        'measurement_period': MeasurementPeriod.CALENDAR_YEAR,
        'effective_date': date(2019, 3, 1),
        'description': 'South Dakota economic nexus: $100k OR 200 transactions (Wayfair origin)',
        'registration_threshold_days': 60
    },
    {
        'state_code': 'TN',
        'nexus_type': 'economic',
        'sales_threshold': 100000.00,
        'transaction_threshold': None,
        'threshold_type': ThresholdMeasurement.SALES_ONLY,
        'measurement_period': MeasurementPeriod.ROLLING_12_MONTHS,
        'effective_date': date(2020, 7, 1),
        'description': 'Tennessee economic nexus: $100,000 in sales',
        'registration_threshold_days': 30
    },
    {
        'state_code': 'TX',
        'nexus_type': 'economic',
        'sales_threshold': 500000.00,
        'transaction_threshold': None,
        'threshold_type': ThresholdMeasurement.SALES_ONLY,
        'measurement_period': MeasurementPeriod.ROLLING_12_MONTHS,
        'effective_date': date(2019, 10, 1),
        'description': 'Texas economic nexus: $500,000 in sales',
        'registration_threshold_days': 30
    },
    {
        'state_code': 'UT',
        'nexus_type': 'economic',
        'sales_threshold': 100000.00,
        'transaction_threshold': 200,
        'threshold_type': ThresholdMeasurement.EITHER,
        'measurement_period': MeasurementPeriod.PREVIOUS_CALENDAR_YEAR,
        'effective_date': date(2019, 10, 1),
        'description': 'Utah economic nexus: $100k OR 200 transactions',
        'registration_threshold_days': 60
    },
    {
        'state_code': 'VT',
        'nexus_type': 'economic',
        'sales_threshold': 100000.00,
        'transaction_threshold': 200,
        'threshold_type': ThresholdMeasurement.EITHER,
        'measurement_period': MeasurementPeriod.CALENDAR_YEAR,
        'effective_date': date(2019, 7, 1),
        'description': 'Vermont economic nexus: $100k OR 200 transactions',
        'registration_threshold_days': 30
    },
    {
        'state_code': 'VA',
        'nexus_type': 'economic',
        'sales_threshold': 100000.00,
        'transaction_threshold': 200,
        'threshold_type': ThresholdMeasurement.EITHER,
        'measurement_period': MeasurementPeriod.PREVIOUS_CALENDAR_YEAR,
        'effective_date': date(2019, 7, 1),
        'description': 'Virginia economic nexus: $100k OR 200 transactions',
        'registration_threshold_days': 60
    },
    {
        'state_code': 'WA',
        'nexus_type': 'economic',
        'sales_threshold': 100000.00,
        'transaction_threshold': None,
        'threshold_type': ThresholdMeasurement.SALES_ONLY,
        'measurement_period': MeasurementPeriod.CALENDAR_YEAR,
        'effective_date': date(2019, 10, 1),
        'description': 'Washington economic nexus: $100,000 in sales',
        'registration_threshold_days': 30
    },
    {
        'state_code': 'WV',
        'nexus_type': 'economic',
        'sales_threshold': 100000.00,
        'transaction_threshold': 200,
        'threshold_type': ThresholdMeasurement.EITHER,
        'measurement_period': MeasurementPeriod.CALENDAR_YEAR,
        'effective_date': date(2019, 1, 1),
        'description': 'West Virginia economic nexus: $100k OR 200 transactions',
        'registration_threshold_days': 60
    },
    {
        'state_code': 'WI',
        'nexus_type': 'economic',
        'sales_threshold': 100000.00,
        'transaction_threshold': None,
        'threshold_type': ThresholdMeasurement.SALES_ONLY,
        'measurement_period': MeasurementPeriod.CALENDAR_YEAR,
        'effective_date': date(2019, 10, 1),
        'description': 'Wisconsin economic nexus: $100,000 in sales',
        'registration_threshold_days': 60
    },
    {
        'state_code': 'WY',
        'nexus_type': 'economic',
        'sales_threshold': 100000.00,
        'transaction_threshold': 200,
        'threshold_type': ThresholdMeasurement.EITHER,
        'measurement_period': MeasurementPeriod.CALENDAR_YEAR,
        'effective_date': date(2019, 7, 1),
        'description': 'Wyoming economic nexus: $100k OR 200 transactions',
        'registration_threshold_days': 60
    },
    {
        'state_code': 'DC',
        'nexus_type': 'economic',
        'sales_threshold': 100000.00,
        'transaction_threshold': 200,
        'threshold_type': ThresholdMeasurement.EITHER,
        'measurement_period': MeasurementPeriod.PREVIOUS_CALENDAR_YEAR,
        'effective_date': date(2019, 1, 1),
        'description': 'DC economic nexus: $100k OR 200 transactions',
        'registration_threshold_days': 60
    }
]


def seed_nexus_rules(db: Session = None):
    """
    Seed nexus_rules table with current economic nexus thresholds.

    Args:
        db: Database session (if None, creates new session)
    """
    if db is None:
        db = SessionLocal()
        should_close = True
    else:
        should_close = False

    try:
        # Check if data already exists
        existing_count = db.query(NexusRule).count()
        if existing_count > 0:
            logger.info(f"Nexus rules already seeded ({existing_count} records)")
            return

        # Insert all rules
        for rule_data in NEXUS_RULES_DATA:
            nexus_rule = NexusRule(**rule_data)
            db.add(nexus_rule)

        db.commit()
        logger.info(f"Successfully seeded {len(NEXUS_RULES_DATA)} nexus rules")

    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding nexus rules: {e}")
        raise

    finally:
        if should_close:
            db.close()


if __name__ == "__main__":
    """Run seed script directly."""
    logging.basicConfig(level=logging.INFO)
    seed_nexus_rules()
    print("Nexus rules seed complete!")

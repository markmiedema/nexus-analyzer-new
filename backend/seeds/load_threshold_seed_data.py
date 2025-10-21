"""
Load state threshold seed data from JavaScript/JSON format.
Loads 45 states with thresholds, tax rates, and interest/penalty data.

Usage:
    python seeds/load_threshold_seed_data.py --replace
"""

import json
import logging
import argparse
import sys
import os
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any

# Add parent directory to path so we can import models
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from models.nexus_rule import NexusRule, NexusType, ThresholdMeasurement, MeasurementPeriod
from models.state_tax_config import StateTaxConfig
from database import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Mapping of window strings to MeasurementPeriod enum
MEASUREMENT_WINDOW_MAP = {
    "rolling_12_months": MeasurementPeriod.ROLLING_12_MONTHS,
    "trailing_12_months": MeasurementPeriod.ROLLING_12_MONTHS,
    "current_or_prior_year": MeasurementPeriod.CURRENT_OR_PRIOR_YEAR,
    "prior_calendar_year": MeasurementPeriod.PRIOR_CALENDAR_YEAR,
    "calendar_year": MeasurementPeriod.CALENDAR_YEAR,
    "trailing_4_quarters": MeasurementPeriod.TRAILING_4_QUARTERS,
    "quarterly_reviewed_12_months": MeasurementPeriod.ROLLING_12_MONTHS,  # Close enough
}


def parse_threshold_data(state_code: str, state_data: Dict[str, Any], db: Session, replace: bool = False):
    """
    Parse and load threshold data for a single state.

    Args:
        state_code: Two-letter state code (e.g., "TX", "CA")
        state_data: Dictionary containing state thresholds and tax data
        db: Database session
        replace: If True, delete existing rules for this state first
    """
    state_name = state_data.get("name")

    if replace:
        # Delete existing rules for this state
        deleted = db.query(NexusRule).filter(NexusRule.state_code == state_code).delete()
        logger.info(f"Deleted {deleted} existing rules for {state_code}")

        # Delete existing tax config for this state
        deleted_tax = db.query(StateTaxConfig).filter(StateTaxConfig.state_code == state_code).delete()
        logger.info(f"Deleted {deleted_tax} existing tax configs for {state_code}")

    # Load nexus rules
    rules_loaded = 0
    for threshold_data in state_data.get("thresholds", []):
        try:
            # Parse effective date
            effective_date = datetime.strptime(threshold_data["effective_date"], "%Y-%m-%d").date()

            # Parse measurement window
            window_str = threshold_data.get("window", "rolling_12_months")
            measurement_window = MEASUREMENT_WINDOW_MAP.get(
                window_str,
                MeasurementPeriod.ROLLING_12_MONTHS
            )

            # Determine threshold measurement
            sales_threshold = threshold_data.get("sales_threshold")
            txn_threshold = threshold_data.get("transaction_threshold")
            operator = threshold_data.get("operator", "or").upper()

            if sales_threshold and txn_threshold:
                if operator == "AND":
                    measurement = ThresholdMeasurement.SALES_AND_TRANSACTIONS
                else:
                    measurement = ThresholdMeasurement.SALES_OR_TRANSACTIONS
            elif sales_threshold:
                measurement = ThresholdMeasurement.SALES_ONLY
            elif txn_threshold:
                measurement = ThresholdMeasurement.TRANSACTIONS_ONLY
            else:
                logger.warning(f"No threshold values for {state_code}, skipping")
                continue

            # Create nexus rule
            rule = NexusRule(
                state_code=state_code,
                state_name=state_name,
                nexus_type=NexusType.ECONOMIC,
                effective_date=effective_date,
                sales_threshold=Decimal(str(sales_threshold)) if sales_threshold else None,
                transaction_threshold=txn_threshold,
                measurement_period=measurement_window,
                threshold_measurement=measurement
            )

            db.add(rule)
            rules_loaded += 1

            # Log the rule
            sales_str = f"${sales_threshold:,.0f}" if sales_threshold else "N/A"
            txn_str = f"{txn_threshold}" if txn_threshold else "N/A"
            logger.info(f"  Added {state_code} rule: {sales_str} sales, {txn_str} txns, effective {effective_date}")

        except Exception as e:
            logger.error(f"Error processing threshold for {state_code}: {e}")
            continue

    # Load state tax config
    tax_rate_data = state_data.get("tax_rate", {})
    interest_penalty_data = state_data.get("interest_penalty", {})

    if tax_rate_data or interest_penalty_data:
        try:
            combined_avg = tax_rate_data.get("combined_avg", 0)

            tax_config = StateTaxConfig(
                state_code=state_code,
                state_name=state_name,
                state_tax_rate=Decimal(str(combined_avg)),  # Using combined_avg as state rate
                avg_local_tax_rate=Decimal("0.00"),  # Will be calculated from ZIP data later
                interest_rate_annual=Decimal(str(interest_penalty_data.get("annual_interest_rate", 0))),
                late_payment_penalty_rate=Decimal(str(interest_penalty_data.get("penalty_rate", 0) * 100))  # Convert to percentage
            )

            db.add(tax_config)
            logger.info(f"  Added {state_code} tax config: {combined_avg:.2%} combined rate")

        except Exception as e:
            logger.error(f"Error processing tax config for {state_code}: {e}")

    # Commit this state's data
    try:
        db.commit()
        logger.info(f"Successfully committed {rules_loaded} rules for {state_code}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error committing data for {state_code}: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(description="Load state threshold seed data")
    parser.add_argument("--replace", action="store_true", help="Replace existing rules")
    args = parser.parse_args()

    # Embedded threshold data (45 states)
    THRESHOLDS = {
        "TX": {"name": "Texas", "thresholds": [{"effective_date": "2019-10-01", "sales_threshold": 500000, "transaction_threshold": None, "window": "rolling_12_months", "operator": "or"}], "tax_rate": {"combined_avg": 0.0819}, "interest_penalty": {"annual_interest_rate": 0.06, "penalty_rate": 0.25}},
        "CA": {"name": "California", "thresholds": [{"effective_date": "2019-04-01", "sales_threshold": 500000, "transaction_threshold": None, "window": "current_or_prior_year", "operator": "or"}], "tax_rate": {"combined_avg": 0.0894}, "interest_penalty": {"annual_interest_rate": 0.07, "penalty_rate": 0.25}},
        "NY": {"name": "New York", "thresholds": [{"effective_date": "2019-06-21", "sales_threshold": 500000, "transaction_threshold": 100, "window": "trailing_4_quarters", "operator": "and"}], "tax_rate": {"combined_avg": 0.0853}, "interest_penalty": {"annual_interest_rate": 0.08, "penalty_rate": 0.20}},
        "FL": {"name": "Florida", "thresholds": [{"effective_date": "2021-07-01", "sales_threshold": 100000, "transaction_threshold": None, "window": "calendar_year", "operator": "or"}], "tax_rate": {"combined_avg": 0.0707}, "interest_penalty": {"annual_interest_rate": 0.09, "penalty_rate": 0.25}},
        "WA": {"name": "Washington", "thresholds": [{"effective_date": "2020-01-01", "sales_threshold": 100000, "transaction_threshold": None, "window": "current_or_prior_year", "operator": "or"}], "tax_rate": {"combined_avg": 0.0925}, "interest_penalty": {"annual_interest_rate": 0.06, "penalty_rate": 0.25}},
        "PA": {"name": "Pennsylvania", "thresholds": [{"effective_date": "2019-07-01", "sales_threshold": 100000, "transaction_threshold": None, "window": "rolling_12_months", "operator": "or"}], "tax_rate": {"combined_avg": 0.0634}, "interest_penalty": {"annual_interest_rate": 0.05, "penalty_rate": 0.20}},
        "IL": {"name": "Illinois", "thresholds": [{"effective_date": "2021-01-01", "sales_threshold": 100000, "transaction_threshold": 200, "window": "trailing_12_months", "operator": "or"}], "tax_rate": {"combined_avg": 0.0889}, "interest_penalty": {"annual_interest_rate": 0.06, "penalty_rate": 0.20}},
        "OH": {"name": "Ohio", "thresholds": [{"effective_date": "2019-08-01", "sales_threshold": 100000, "transaction_threshold": 200, "window": "current_or_prior_year", "operator": "or"}], "tax_rate": {"combined_avg": 0.0751}, "interest_penalty": {"annual_interest_rate": 0.05, "penalty_rate": 0.20}},
        "GA": {"name": "Georgia", "thresholds": [{"effective_date": "2020-01-01", "sales_threshold": 100000, "transaction_threshold": 200, "window": "current_or_prior_year", "operator": "or"}], "tax_rate": {"combined_avg": 0.0759}, "interest_penalty": {"annual_interest_rate": 0.06, "penalty_rate": 0.25}},
        "MA": {"name": "Massachusetts", "thresholds": [{"effective_date": "2019-10-01", "sales_threshold": 100000, "transaction_threshold": None, "window": "current_or_prior_year", "operator": "or"}], "tax_rate": {"combined_avg": 0.0625}, "interest_penalty": {"annual_interest_rate": 0.08, "penalty_rate": 0.25}},
        "AZ": {"name": "Arizona", "thresholds": [{"effective_date": "2019-10-01", "sales_threshold": 100000, "transaction_threshold": None, "window": "current_or_prior_year", "operator": "or"}], "tax_rate": {"combined_avg": 0.0841}, "interest_penalty": {"annual_interest_rate": 0.06, "penalty_rate": 0.25}},
        "CO": {"name": "Colorado", "thresholds": [{"effective_date": "2019-06-01", "sales_threshold": 100000, "transaction_threshold": None, "window": "current_or_prior_year", "operator": "or"}], "tax_rate": {"combined_avg": 0.0781}, "interest_penalty": {"annual_interest_rate": 0.06, "penalty_rate": 0.25}},
        "TN": {"name": "Tennessee", "thresholds": [{"effective_date": "2019-10-01", "sales_threshold": 100000, "transaction_threshold": None, "window": "rolling_12_months", "operator": "or"}], "tax_rate": {"combined_avg": 0.0956}, "interest_penalty": {"annual_interest_rate": 0.07, "penalty_rate": 0.25}},
        "NC": {"name": "North Carolina", "thresholds": [{"effective_date": "2019-11-01", "sales_threshold": 100000, "transaction_threshold": None, "window": "current_or_prior_year", "operator": "or"}], "tax_rate": {"combined_avg": 0.07}, "interest_penalty": {"annual_interest_rate": 0.06, "penalty_rate": 0.25}},
        "KS": {"name": "Kansas", "thresholds": [{"effective_date": "2021-07-01", "sales_threshold": 100000, "transaction_threshold": None, "window": "current_or_prior_year", "operator": "or"}], "tax_rate": {"combined_avg": 0.0877}, "interest_penalty": {"annual_interest_rate": 0.09, "penalty_rate": 0.24}},
        "NJ": {"name": "New Jersey", "thresholds": [{"effective_date": "2019-11-01", "sales_threshold": 100000, "transaction_threshold": 200, "window": "current_or_prior_year", "operator": "or"}], "tax_rate": {"combined_avg": 0.06625}, "interest_penalty": {"annual_interest_rate": 0.08, "penalty_rate": 0.25}},
        "WI": {"name": "Wisconsin", "thresholds": [{"effective_date": "2019-10-01", "sales_threshold": 100000, "transaction_threshold": None, "window": "current_or_prior_year", "operator": "or"}], "tax_rate": {"combined_avg": 0.057}, "interest_penalty": {"annual_interest_rate": 0.05, "penalty_rate": 0.25}},
        "ME": {"name": "Maine", "thresholds": [{"effective_date": "2018-07-01", "sales_threshold": 100000, "transaction_threshold": 200, "window": "current_or_prior_year", "operator": "or"}], "tax_rate": {"combined_avg": 0.055}, "interest_penalty": {"annual_interest_rate": 0.10, "penalty_rate": 0.25}},
        "NM": {"name": "New Mexico", "thresholds": [{"effective_date": "2019-07-01", "sales_threshold": 100000, "transaction_threshold": None, "window": "calendar_year", "operator": "or"}], "tax_rate": {"combined_avg": 0.07625}, "interest_penalty": {"annual_interest_rate": 0.07, "penalty_rate": 0.20}},
        "AL": {"name": "Alabama", "thresholds": [{"effective_date": "2018-10-01", "sales_threshold": 250000, "transaction_threshold": None, "window": "prior_calendar_year", "operator": "or"}], "tax_rate": {"combined_avg": 0.0929}, "interest_penalty": {"annual_interest_rate": 0.07, "penalty_rate": 0.20}},
        "CT": {"name": "Connecticut", "thresholds": [{"effective_date": "2019-12-01", "sales_threshold": 100000, "transaction_threshold": 200, "window": "rolling_12_months", "operator": "and"}], "tax_rate": {"combined_avg": 0.0635}, "interest_penalty": {"annual_interest_rate": 0.07, "penalty_rate": 0.25}},
        "IN": {"name": "Indiana", "thresholds": [{"effective_date": "2019-10-01", "sales_threshold": 100000, "transaction_threshold": None, "window": "current_or_prior_year", "operator": "or"}], "tax_rate": {"combined_avg": 0.07}, "interest_penalty": {"annual_interest_rate": 0.06, "penalty_rate": 0.20}},
        "KY": {"name": "Kentucky", "thresholds": [{"effective_date": "2019-07-01", "sales_threshold": 100000, "transaction_threshold": 200, "window": "current_or_prior_year", "operator": "or"}], "tax_rate": {"combined_avg": 0.06}, "interest_penalty": {"annual_interest_rate": 0.06, "penalty_rate": 0.20}},
        "LA": {"name": "Louisiana", "thresholds": [{"effective_date": "2020-07-01", "sales_threshold": 100000, "transaction_threshold": None, "window": "current_or_prior_year", "operator": "or"}], "tax_rate": {"combined_avg": 0.1012}, "interest_penalty": {"annual_interest_rate": 0.08, "penalty_rate": 0.25}},
        "MD": {"name": "Maryland", "thresholds": [{"effective_date": "2019-10-01", "sales_threshold": 100000, "transaction_threshold": 200, "window": "current_or_prior_year", "operator": "or"}], "tax_rate": {"combined_avg": 0.06}, "interest_penalty": {"annual_interest_rate": 0.07, "penalty_rate": 0.25}},
        "MI": {"name": "Michigan", "thresholds": [{"effective_date": "2019-10-01", "sales_threshold": 100000, "transaction_threshold": 200, "window": "calendar_year", "operator": "or"}], "tax_rate": {"combined_avg": 0.06}, "interest_penalty": {"annual_interest_rate": 0.05, "penalty_rate": 0.25}},
        "MN": {"name": "Minnesota", "thresholds": [{"effective_date": "2019-10-01", "sales_threshold": 100000, "transaction_threshold": 200, "window": "rolling_12_months", "operator": "or"}], "tax_rate": {"combined_avg": 0.0813}, "interest_penalty": {"annual_interest_rate": 0.06, "penalty_rate": 0.20}},
        "NV": {"name": "Nevada", "thresholds": [{"effective_date": "2019-10-01", "sales_threshold": 100000, "transaction_threshold": 200, "window": "current_or_prior_year", "operator": "or"}], "tax_rate": {"combined_avg": 0.0824}, "interest_penalty": {"annual_interest_rate": 0.07, "penalty_rate": 0.25}},
        "VA": {"name": "Virginia", "thresholds": [{"effective_date": "2019-07-01", "sales_threshold": 100000, "transaction_threshold": 200, "window": "current_or_prior_year", "operator": "or"}], "tax_rate": {"combined_avg": 0.0577}, "interest_penalty": {"annual_interest_rate": 0.06, "penalty_rate": 0.20}},
        "AR": {"name": "Arkansas", "thresholds": [{"effective_date": "2019-07-01", "sales_threshold": 100000, "transaction_threshold": 200, "window": "current_or_prior_year", "operator": "or"}], "tax_rate": {"combined_avg": 0.0945}, "interest_penalty": {"annual_interest_rate": 0.10, "penalty_rate": 0.35}},
        "HI": {"name": "Hawaii", "thresholds": [{"effective_date": "2020-01-01", "sales_threshold": 100000, "transaction_threshold": 200, "window": "current_or_prior_year", "operator": "or"}], "tax_rate": {"combined_avg": 0.045}, "interest_penalty": {"annual_interest_rate": 0.08, "penalty_rate": 0.25}},
        "ID": {"name": "Idaho", "thresholds": [{"effective_date": "2019-06-01", "sales_threshold": 100000, "transaction_threshold": None, "window": "current_or_prior_year", "operator": "or"}], "tax_rate": {"combined_avg": 0.0603}, "interest_penalty": {"annual_interest_rate": 0.06, "penalty_rate": 0.25}},
        "IA": {"name": "Iowa", "thresholds": [{"effective_date": "2019-01-01", "sales_threshold": 100000, "transaction_threshold": None, "window": "current_or_prior_year", "operator": "or"}], "tax_rate": {"combined_avg": 0.0694}, "interest_penalty": {"annual_interest_rate": 0.10, "penalty_rate": 0.10}},
        "MS": {"name": "Mississippi", "thresholds": [{"effective_date": "2020-07-01", "sales_threshold": 250000, "transaction_threshold": None, "window": "rolling_12_months", "operator": "or"}], "tax_rate": {"combined_avg": 0.0706}, "interest_penalty": {"annual_interest_rate": 0.12, "penalty_rate": 0.20}},
        "MO": {"name": "Missouri", "thresholds": [{"effective_date": "2023-01-01", "sales_threshold": 100000, "transaction_threshold": None, "window": "quarterly_reviewed_12_months", "operator": "or"}], "tax_rate": {"combined_avg": 0.08415}, "interest_penalty": {"annual_interest_rate": 0.04, "penalty_rate": 0.25}},
        "NE": {"name": "Nebraska", "thresholds": [{"effective_date": "2019-01-01", "sales_threshold": 100000, "transaction_threshold": 200, "window": "current_or_prior_year", "operator": "or"}], "tax_rate": {"combined_avg": 0.0698}, "interest_penalty": {"annual_interest_rate": 0.08, "penalty_rate": 0.10}},
        "ND": {"name": "North Dakota", "thresholds": [{"effective_date": "2018-10-01", "sales_threshold": 100000, "transaction_threshold": None, "window": "current_or_prior_year", "operator": "or"}], "tax_rate": {"combined_avg": 0.0705}, "interest_penalty": {"annual_interest_rate": 0.12, "penalty_rate": 0.25}},
        "OK": {"name": "Oklahoma", "thresholds": [{"effective_date": "2019-11-01", "sales_threshold": 100000, "transaction_threshold": None, "window": "current_or_prior_year", "operator": "or"}], "tax_rate": {"combined_avg": 0.09}, "interest_penalty": {"annual_interest_rate": 0.15, "penalty_rate": 0.10}},
        "RI": {"name": "Rhode Island", "thresholds": [{"effective_date": "2017-07-15", "sales_threshold": 100000, "transaction_threshold": 200, "window": "calendar_year", "operator": "or"}], "tax_rate": {"combined_avg": 0.07}, "interest_penalty": {"annual_interest_rate": 0.12, "penalty_rate": 0.10}},
        "SC": {"name": "South Carolina", "thresholds": [{"effective_date": "2018-10-01", "sales_threshold": 100000, "transaction_threshold": None, "window": "current_or_prior_year", "operator": "or"}], "tax_rate": {"combined_avg": 0.075}, "interest_penalty": {"annual_interest_rate": 0.00, "penalty_rate": 0.50}},
        "SD": {"name": "South Dakota", "thresholds": [{"effective_date": "2018-11-01", "sales_threshold": 100000, "transaction_threshold": None, "window": "current_or_prior_year", "operator": "or"}], "tax_rate": {"combined_avg": 0.0611}, "interest_penalty": {"annual_interest_rate": 0.12, "penalty_rate": 0.10}},
        "UT": {"name": "Utah", "thresholds": [{"effective_date": "2019-01-01", "sales_threshold": 100000, "transaction_threshold": 200, "window": "current_or_prior_year", "operator": "or"}], "tax_rate": {"combined_avg": 0.0732}, "interest_penalty": {"annual_interest_rate": 0.06, "penalty_rate": 0.10}},
        "VT": {"name": "Vermont", "thresholds": [{"effective_date": "2018-07-01", "sales_threshold": 100000, "transaction_threshold": 200, "window": "trailing_4_quarters", "operator": "or"}], "tax_rate": {"combined_avg": 0.0637}, "interest_penalty": {"annual_interest_rate": 0.18, "penalty_rate": 0.25}},
        "WV": {"name": "West Virginia", "thresholds": [{"effective_date": "2019-01-01", "sales_threshold": 100000, "transaction_threshold": 200, "window": "current_or_prior_year", "operator": "or"}], "tax_rate": {"combined_avg": 0.0657}, "interest_penalty": {"annual_interest_rate": 0.1225, "penalty_rate": 0.50}},
        "WY": {"name": "Wyoming", "thresholds": [{"effective_date": "2019-02-01", "sales_threshold": 100000, "transaction_threshold": 200, "window": "current_or_prior_year", "operator": "or"}], "tax_rate": {"combined_avg": 0.0544}, "interest_penalty": {"annual_interest_rate": 0.12, "penalty_rate": 0.10}}
    }

    db = SessionLocal()

    try:
        logger.info(f"Found {len(THRESHOLDS)} states to process")

        total_rules = 0
        summary = {}

        for state_code, state_data in sorted(THRESHOLDS.items()):
            logger.info(f"\nProcessing {state_code} - {state_data['name']}")
            parse_threshold_data(state_code, state_data, db, args.replace)

            # Count rules for summary
            rule_count = len(state_data.get("thresholds", []))
            total_rules += rule_count
            summary[state_code] = rule_count

        logger.info("\n" + "=" * 60)
        logger.info("SUMMARY")
        logger.info("=" * 60)
        for state_code, count in sorted(summary.items()):
            logger.info(f"  {state_code}: {count} rule(s)")
        logger.info("=" * 60)
        logger.info(f"  TOTAL: {total_rules} rules across {len(THRESHOLDS)} states")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error loading threshold data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

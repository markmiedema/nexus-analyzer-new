"""
Load proprietary state nexus rules from JSON files.
Reads user's detailed state research data from D:\SALT\State Information_October\

This script imports lawyer-grade state research data including:
- Legal citations
- Multiple historical threshold periods
- Marketplace facilitator rules
- Registration timing rules
- QA test vectors
- Confidence scores

Usage:
    python seeds/load_proprietary_state_rules.py --data-dir "D:\SALT\State Information_October"

    Or from Docker:
    docker-compose exec backend python seeds/load_proprietary_state_rules.py --data-dir "/mnt/state_data"
"""

import json
import logging
from pathlib import Path
from datetime import datetime, date
from typing import Dict, List, Optional
import argparse
import sys
import os

# Add parent directory to path so we can import models
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from models.nexus_rule import (
    NexusRule,
    NexusType,
    ThresholdMeasurement,
    MeasurementPeriod
)
from database import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_measurement_window(window_str: str) -> MeasurementPeriod:
    """
    Map JSON measurement window strings to MeasurementPeriod enum.

    Args:
        window_str: String like "rolling_12_months", "calendar_year", etc.

    Returns:
        MeasurementPeriod enum value
    """
    mapping = {
        "rolling_12_months": MeasurementPeriod.ROLLING_12_MONTHS,
        "calendar_year": MeasurementPeriod.CALENDAR_YEAR,
        "previous_calendar_year": MeasurementPeriod.PREVIOUS_CALENDAR_YEAR,
        "trailing_12_months": MeasurementPeriod.ROLLING_12_MONTHS,  # Alias
    }

    result = mapping.get(window_str.lower(), MeasurementPeriod.ROLLING_12_MONTHS)

    if window_str.lower() not in mapping:
        logger.warning(
            f"Unknown measurement window '{window_str}', defaulting to ROLLING_12_MONTHS"
        )

    return result


def parse_threshold_measurement(threshold_data: Dict) -> ThresholdMeasurement:
    """
    Determine ThresholdMeasurement enum from threshold data.

    Args:
        threshold_data: Dictionary containing sales_threshold and/or transaction_threshold

    Returns:
        ThresholdMeasurement enum value
    """
    has_sales = threshold_data.get("sales_threshold") is not None
    has_transactions = threshold_data.get("transaction_threshold") is not None

    # Check if there's a measurement_type field
    measurement_type = threshold_data.get("threshold_type", "").lower()

    if measurement_type == "sales_and_transactions" or measurement_type == "both":
        return ThresholdMeasurement.SALES_AND_TRANSACTIONS
    elif measurement_type == "sales_or_transactions" or measurement_type == "either":
        return ThresholdMeasurement.SALES_OR_TRANSACTIONS

    # Infer from which thresholds are present
    if has_sales and has_transactions:
        # Default to OR logic if both present but not specified
        return ThresholdMeasurement.SALES_OR_TRANSACTIONS
    elif has_sales:
        return ThresholdMeasurement.SALES_ONLY
    elif has_transactions:
        return ThresholdMeasurement.TRANSACTIONS_ONLY
    else:
        logger.warning("No thresholds found, defaulting to SALES_ONLY")
        return ThresholdMeasurement.SALES_ONLY


def parse_date(date_str: str) -> Optional[date]:
    """
    Parse date string in various formats.

    Args:
        date_str: Date string like "2019-01-01" or "2019-10-01"

    Returns:
        date object or None if parsing fails
    """
    if not date_str:
        return None

    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        try:
            return datetime.strptime(date_str, "%m/%d/%Y").date()
        except ValueError:
            logger.error(f"Could not parse date: {date_str}")
            return None


def load_state_json(file_path: Path, db: Session, replace_existing: bool = False) -> int:
    """
    Load a single state's JSON file into the database.

    Args:
        file_path: Path to the JSON file (e.g., Texas.txt)
        db: Database session
        replace_existing: If True, delete existing rules for this state first

    Returns:
        Number of rules inserted
    """
    logger.info(f"Loading state data from: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        return 0
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return 0

    state_code = data.get("state_code")
    if not state_code:
        logger.error(f"No state_code found in {file_path}")
        return 0

    # Delete existing rules for this state if requested
    if replace_existing:
        deleted = db.query(NexusRule).filter(NexusRule.state == state_code).delete()
        logger.info(f"Deleted {deleted} existing rules for {state_code}")

    thresholds = data.get("thresholds", [])
    if not thresholds:
        logger.warning(f"No thresholds found for {state_code}")
        return 0

    rules_inserted = 0

    for threshold in thresholds:
        try:
            # Parse dates
            effective_date = parse_date(threshold.get("effective_date"))
            end_date = parse_date(threshold.get("end_date"))

            if not effective_date:
                logger.warning(f"Skipping threshold with no effective_date in {state_code}")
                continue

            # Extract threshold values
            sales_threshold = threshold.get("sales_threshold")
            transaction_threshold = threshold.get("transaction_threshold")

            # Parse measurement settings
            measurement_window = threshold.get("measurement_window", "rolling_12_months")
            measurement_period = parse_measurement_window(measurement_window)
            threshold_measurement = parse_threshold_measurement(threshold)

            # Marketplace facilitator rules
            marketplace_facilitator_law = threshold.get("marketplace_facilitator_law", False)
            marketplace_sales_excluded = threshold.get("marketplace_sales_excluded", True)

            # Build description from multiple sources
            description_parts = []

            if threshold.get("description"):
                description_parts.append(threshold["description"])

            # Add legal citations if available
            legal_citations = threshold.get("legal_citations", [])
            if legal_citations:
                citations_str = "; ".join(legal_citations[:3])  # First 3 citations
                description_parts.append(f"Legal: {citations_str}")

            # Add confidence score if available
            confidence = threshold.get("confidence_score")
            if confidence:
                description_parts.append(f"Confidence: {confidence}")

            rule_description = " | ".join(description_parts) if description_parts else None

            # Truncate to fit database field (1000 chars)
            if rule_description and len(rule_description) > 1000:
                rule_description = rule_description[:997] + "..."

            # Extract URLs
            registration_url = threshold.get("registration_url")
            rule_source_url = threshold.get("rule_source_url") or threshold.get("source_url")

            # Create NexusRule
            nexus_rule = NexusRule(
                state=state_code,
                nexus_type=NexusType.ECONOMIC,  # Most common; adjust if needed
                sales_threshold=sales_threshold,
                transaction_threshold=transaction_threshold,
                threshold_measurement=threshold_measurement,
                measurement_period=measurement_period,
                marketplace_facilitator_law=marketplace_facilitator_law,
                marketplace_sales_excluded=marketplace_sales_excluded,
                effective_date=effective_date,
                end_date=end_date,
                rule_description=rule_description,
                registration_url=registration_url,
                rule_source_url=rule_source_url
            )

            db.add(nexus_rule)
            rules_inserted += 1

            logger.info(
                f"  Added {state_code} rule: ${sales_threshold or 'N/A'} sales, "
                f"{transaction_threshold or 'N/A'} txns, effective {effective_date}"
            )

        except Exception as e:
            logger.error(f"Error processing threshold in {state_code}: {e}", exc_info=True)
            continue

    try:
        db.commit()
        logger.info(f"Successfully committed {rules_inserted} rules for {state_code}")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to commit {state_code} rules: {e}")
        return 0

    return rules_inserted


def load_all_states(data_dir: Path, db: Session, replace_existing: bool = False) -> Dict[str, int]:
    """
    Load all state JSON files from a directory.

    Args:
        data_dir: Directory containing state JSON files (e.g., Texas.txt, Alabama.txt)
        db: Database session
        replace_existing: If True, replace existing rules for each state

    Returns:
        Dictionary mapping state names to number of rules inserted
    """
    if not data_dir.exists():
        logger.error(f"Data directory not found: {data_dir}")
        return {}

    # Find all .txt or .json files
    state_files = list(data_dir.glob("*.txt")) + list(data_dir.glob("*.json"))

    if not state_files:
        logger.warning(f"No state files found in {data_dir}")
        return {}

    logger.info(f"Found {len(state_files)} state files to process")

    results = {}

    for state_file in sorted(state_files):
        state_name = state_file.stem  # Filename without extension
        count = load_state_json(state_file, db, replace_existing)
        results[state_name] = count

    return results


def main():
    """Main entry point for the seed script."""
    parser = argparse.ArgumentParser(
        description="Load proprietary state nexus rules from JSON files"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        required=True,
        help="Directory containing state JSON files (e.g., D:\\SALT\\State Information_October)"
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace existing rules for each state (default: skip if exists)"
    )
    parser.add_argument(
        "--state",
        type=str,
        help="Load only a specific state file (e.g., Texas.txt)"
    )

    args = parser.parse_args()

    data_dir = Path(args.data_dir)

    db = SessionLocal()

    try:
        if args.state:
            # Load single state
            state_file = data_dir / args.state
            if not state_file.exists():
                logger.error(f"State file not found: {state_file}")
                sys.exit(1)

            count = load_state_json(state_file, db, args.replace)
            logger.info(f"\nLoaded {count} rules from {args.state}")
        else:
            # Load all states
            results = load_all_states(data_dir, db, args.replace)

            # Print summary
            logger.info("\n" + "=" * 60)
            logger.info("SUMMARY")
            logger.info("=" * 60)

            total_rules = 0
            for state_name, count in sorted(results.items()):
                logger.info(f"  {state_name:20s}: {count:3d} rules")
                total_rules += count

            logger.info("=" * 60)
            logger.info(f"  TOTAL:               {total_rules:3d} rules")
            logger.info("=" * 60)

    finally:
        db.close()


if __name__ == "__main__":
    main()
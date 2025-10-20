"""
Load historical tax rate data from CSV files.
Reads ZIP-level tax rate data and aggregates to state level.

Input: 78 CSV files from D:\Nexus Threshold Research\...\split_20250723_212859\
Columns: zipcode, state, county, normalizedcounty, city, normalizedcity,
         taxregionname, normalizedtaxregionname, combinedrate, staterate,
         countyrate, cityrate, specialrate, estimatedpopulation, year, month

Output: Aggregated state-level tax configuration in state_tax_config table

Usage:
    python seeds/load_historical_tax_rates.py --csv-dir "D:\Nexus Threshold Research\...\split_20250723_212859"

    Or from Docker:
    docker-compose exec backend python seeds/load_historical_tax_rates.py --csv-dir "/mnt/tax_data"
"""

import logging
import argparse
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd
from decimal import Decimal

# Add parent directory to path so we can import models
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from sqlalchemy import func
from models.state_tax_config import StateTaxConfig
from database import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# State code to state name mapping
STATE_NAMES = {
    'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
    'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
    'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho',
    'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas',
    'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
    'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
    'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada',
    'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
    'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma',
    'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
    'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah',
    'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia',
    'WI': 'Wisconsin', 'WY': 'Wyoming', 'DC': 'District of Columbia'
}

# States with no sales tax
NO_SALES_TAX_STATES = {'AK', 'DE', 'MT', 'NH', 'OR'}

# States using origin-based sourcing (most use destination-based)
ORIGIN_BASED_STATES = {'AZ', 'CA', 'IL', 'MS', 'MO', 'NM', 'OH', 'PA', 'TN', 'TX', 'UT', 'VA'}


def load_csv_chunks(csv_dir: Path) -> pd.DataFrame:
    """
    Load all CSV chunks from a directory and concatenate them.

    Args:
        csv_dir: Directory containing CSV chunks (chunk_1.csv, chunk_2.csv, etc.)

    Returns:
        Combined DataFrame with all tax rate data
    """
    if not csv_dir.exists():
        logger.error(f"CSV directory not found: {csv_dir}")
        return pd.DataFrame()

    # Find all CSV files
    csv_files = sorted(csv_dir.glob("*.csv"))

    if not csv_files:
        logger.warning(f"No CSV files found in {csv_dir}")
        return pd.DataFrame()

    logger.info(f"Found {len(csv_files)} CSV files to process")

    # Read and concatenate all chunks
    dfs = []
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file, low_memory=False)
            dfs.append(df)
            logger.info(f"  Loaded {csv_file.name}: {len(df):,} rows")
        except Exception as e:
            logger.error(f"Error reading {csv_file}: {e}")
            continue

    if not dfs:
        logger.error("No CSV files successfully loaded")
        return pd.DataFrame()

    combined_df = pd.concat(dfs, ignore_index=True)
    logger.info(f"Combined dataset: {len(combined_df):,} rows")

    return combined_df


def clean_rate_column(df: pd.DataFrame, column: str) -> pd.Series:
    """
    Clean and convert rate column to decimal.
    Handles percentages (6.5) and decimals (0.065).

    Args:
        df: DataFrame
        column: Column name

    Returns:
        Series with cleaned decimal rates
    """
    if column not in df.columns:
        return pd.Series([0.0] * len(df))

    rates = pd.to_numeric(df[column], errors='coerce').fillna(0)

    # If values are > 1, assume they're percentages (e.g., 6.5 = 6.5%)
    # Convert to decimal (0.065)
    rates = rates.apply(lambda x: x / 100 if x > 1 else x)

    return rates


def aggregate_state_data(df: pd.DataFrame) -> Dict[str, Dict]:
    """
    Aggregate ZIP-level data to state level.

    For each state, calculate:
    - Average state tax rate (should be consistent)
    - Average local tax rate (county + city + special)
    - Min/max combined rates
    - Whether state has local taxes

    Args:
        df: DataFrame with tax rate data

    Returns:
        Dictionary mapping state codes to aggregated data
    """
    if df.empty:
        return {}

    # Clean rate columns
    df['staterate_clean'] = clean_rate_column(df, 'staterate')
    df['countyrate_clean'] = clean_rate_column(df, 'countyrate')
    df['cityrate_clean'] = clean_rate_column(df, 'cityrate')
    df['specialrate_clean'] = clean_rate_column(df, 'specialrate')
    df['combinedrate_clean'] = clean_rate_column(df, 'combinedrate')

    # Calculate local rate (county + city + special)
    df['localrate'] = (
        df['countyrate_clean'] +
        df['cityrate_clean'] +
        df['specialrate_clean']
    )

    # Get most recent data (latest year and month)
    if 'year' in df.columns and 'month' in df.columns:
        df['year'] = pd.to_numeric(df['year'], errors='coerce')
        df['month'] = pd.to_numeric(df['month'], errors='coerce')

        # Filter to most recent year/month
        max_year = df['year'].max()
        recent_df = df[df['year'] == max_year]

        if not recent_df.empty:
            max_month = recent_df['month'].max()
            recent_df = recent_df[recent_df['month'] == max_month]
            logger.info(f"Using most recent data: {int(max_year)}-{int(max_month):02d}")
            df = recent_df

    # Aggregate by state
    state_data = {}

    for state_code in df['state'].unique():
        if pd.isna(state_code) or state_code == '':
            continue

        state_code = str(state_code).strip().upper()

        if len(state_code) != 2:
            continue

        state_df = df[df['state'] == state_code]

        # Calculate aggregates
        state_tax_rate = state_df['staterate_clean'].mean()
        avg_local_rate = state_df['localrate'].mean()
        min_combined = state_df['combinedrate_clean'].min()
        max_combined = state_df['combinedrate_clean'].max()

        # Check if state has local taxes (any non-zero local rate)
        has_local_taxes = (state_df['localrate'] > 0).any()

        state_data[state_code] = {
            'state_name': STATE_NAMES.get(state_code, f"Unknown ({state_code})"),
            'state_tax_rate': round(state_tax_rate, 4),
            'avg_local_tax_rate': round(avg_local_rate, 4),
            'min_combined_rate': round(min_combined, 4),
            'max_combined_rate': round(max_combined, 4),
            'has_local_taxes': has_local_taxes,
            'sample_size': len(state_df)
        }

    return state_data


def create_state_tax_config(
    state_code: str,
    state_data: Dict,
    db: Session,
    replace_existing: bool = False
) -> bool:
    """
    Create or update a StateTaxConfig record.

    Args:
        state_code: Two-letter state code
        state_data: Aggregated state data
        db: Database session
        replace_existing: If True, replace existing record

    Returns:
        True if successful, False otherwise
    """
    try:
        # Check if record exists
        existing = db.query(StateTaxConfig).filter(
            StateTaxConfig.state_code == state_code
        ).first()

        if existing:
            if replace_existing:
                logger.info(f"  Updating existing record for {state_code}")
                for key, value in state_data.items():
                    if key != 'sample_size':  # Don't store sample_size in DB
                        setattr(existing, key, value)
            else:
                logger.info(f"  Skipping {state_code} (already exists)")
                return False
        else:
            # Create new record
            config = StateTaxConfig(
                state_code=state_code,
                state_name=state_data['state_name'],
                state_tax_rate=Decimal(str(state_data['state_tax_rate'])),
                avg_local_tax_rate=Decimal(str(state_data['avg_local_tax_rate'])),
                min_combined_rate=Decimal(str(state_data['min_combined_rate'])),
                max_combined_rate=Decimal(str(state_data['max_combined_rate'])),
                has_sales_tax=state_code not in NO_SALES_TAX_STATES,
                has_local_taxes=state_data['has_local_taxes'],
                is_destination_based=state_code not in ORIGIN_BASED_STATES,
                is_origin_based=state_code in ORIGIN_BASED_STATES,
                sales_tax_name="Sales and Use Tax",  # Default
                local_tax_administered_by_state=True,  # Default (varies by state)
            )

            db.add(config)
            logger.info(
                f"  Added {state_code}: {state_data['state_tax_rate']:.2%} state, "
                f"{state_data['avg_local_tax_rate']:.2%} avg local "
                f"({state_data['sample_size']:,} ZIP codes)"
            )

        return True

    except Exception as e:
        logger.error(f"Error creating StateTaxConfig for {state_code}: {e}", exc_info=True)
        return False


def load_tax_rates(
    csv_dir: Path,
    db: Session,
    replace_existing: bool = False
) -> Tuple[int, int]:
    """
    Load tax rate data from CSV files into database.

    Args:
        csv_dir: Directory containing CSV chunks
        db: Database session
        replace_existing: If True, replace existing records

    Returns:
        Tuple of (states_loaded, states_skipped)
    """
    # Load and combine CSV files
    df = load_csv_chunks(csv_dir)

    if df.empty:
        logger.error("No data loaded from CSV files")
        return 0, 0

    # Aggregate by state
    logger.info("\nAggregating data by state...")
    state_data = aggregate_state_data(df)

    if not state_data:
        logger.error("No state data aggregated")
        return 0, 0

    logger.info(f"Aggregated data for {len(state_data)} states")

    # Insert into database
    logger.info("\nInserting into database...")
    loaded = 0
    skipped = 0

    for state_code, data in sorted(state_data.items()):
        if create_state_tax_config(state_code, data, db, replace_existing):
            loaded += 1
        else:
            skipped += 1

    # Commit transaction
    try:
        db.commit()
        logger.info(f"\nSuccessfully committed {loaded} state tax configs")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to commit: {e}")
        return 0, loaded + skipped

    return loaded, skipped


def main():
    """Main entry point for the seed script."""
    parser = argparse.ArgumentParser(
        description="Load historical tax rate data from CSV files"
    )
    parser.add_argument(
        "--csv-dir",
        type=str,
        required=True,
        help="Directory containing CSV chunks (e.g., D:\\Nexus Threshold Research\\...\\split_20250723_212859)"
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace existing state tax configs (default: skip if exists)"
    )

    args = parser.parse_args()

    csv_dir = Path(args.csv_dir)

    if not csv_dir.exists():
        logger.error(f"CSV directory not found: {csv_dir}")
        sys.exit(1)

    db = SessionLocal()

    try:
        loaded, skipped = load_tax_rates(csv_dir, db, args.replace)

        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("SUMMARY")
        logger.info("=" * 60)
        logger.info(f"  States loaded:  {loaded:3d}")
        logger.info(f"  States skipped: {skipped:3d}")
        logger.info(f"  Total states:   {loaded + skipped:3d}")
        logger.info("=" * 60)

        # Query and display results
        logger.info("\nSample of loaded data:")
        logger.info("-" * 60)

        configs = db.query(StateTaxConfig).order_by(StateTaxConfig.state_code).limit(10).all()

        for config in configs:
            logger.info(
                f"{config.state_code} - {config.state_name:20s}: "
                f"{float(config.state_tax_rate):6.2%} state, "
                f"{float(config.avg_local_tax_rate):6.2%} avg local, "
                f"range: {float(config.min_combined_rate):6.2%} - {float(config.max_combined_rate):6.2%}"
            )

    finally:
        db.close()


if __name__ == "__main__":
    main()
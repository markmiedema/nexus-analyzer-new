"""
CSV processing service with parsing, validation, and data normalization.
"""

import csv
import io
import chardet
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from decimal import Decimal, InvalidOperation
import logging
from sqlalchemy.orm import Session

from models.transaction import Transaction
from models.analysis import Analysis, AnalysisStatus

logger = logging.getLogger(__name__)

# State code mappings (abbreviation to full name and vice versa)
STATE_CODES = {
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

# Reverse mapping
STATE_NAMES_TO_CODES = {v.upper(): k for k, v in STATE_CODES.items()}


class ColumnMapping:
    """Column name mappings for different CSV formats."""

    # Date column aliases
    DATE_COLUMNS = [
        'date', 'transaction_date', 'order_date', 'sale_date',
        'invoice_date', 'Date', 'Transaction Date', 'Order Date'
    ]

    # State column aliases
    STATE_COLUMNS = [
        'state', 'customer_state', 'ship_to_state', 'destination_state',
        'State', 'Customer State', 'Ship To State', 'Billing State'
    ]

    # Amount column aliases
    AMOUNT_COLUMNS = [
        'amount', 'total', 'gross_amount', 'sale_amount', 'revenue',
        'Amount', 'Total', 'Gross Amount', 'Sale Amount', 'Revenue'
    ]

    # Tax collected column aliases
    TAX_COLUMNS = [
        'tax', 'tax_collected', 'sales_tax', 'tax_amount',
        'Tax', 'Tax Collected', 'Sales Tax', 'Tax Amount'
    ]

    # Shipping column aliases
    SHIPPING_COLUMNS = [
        'shipping', 'shipping_amount', 'freight', 'shipping_cost',
        'Shipping', 'Shipping Amount', 'Freight'
    ]

    # Order ID column aliases
    ORDER_ID_COLUMNS = [
        'order_id', 'transaction_id', 'invoice_number', 'order_number',
        'Order ID', 'Transaction ID', 'Invoice Number'
    ]

    # Customer ID column aliases
    CUSTOMER_ID_COLUMNS = [
        'customer_id', 'customer', 'customer_number',
        'Customer ID', 'Customer', 'Customer Number'
    ]

    # Marketplace columns
    MARKETPLACE_COLUMNS = [
        'marketplace', 'marketplace_name', 'channel', 'platform',
        'Marketplace', 'Channel', 'Platform'
    ]

    # Exemption columns
    EXEMPT_COLUMNS = [
        'exempt', 'is_exempt', 'tax_exempt', 'exemption',
        'Exempt', 'Tax Exempt', 'Exemption'
    ]


class CSVProcessor:
    """Process and validate CSV files for transaction data."""

    def __init__(self):
        self.column_mapping = ColumnMapping()
        self.validation_errors: List[Dict] = []
        self.valid_row_count = 0
        self.invalid_row_count = 0

    def detect_encoding(self, file_content: bytes) -> str:
        """
        Detect file encoding using chardet.

        Args:
            file_content: Raw file bytes

        Returns:
            str: Detected encoding (e.g., 'utf-8', 'latin-1')
        """
        result = chardet.detect(file_content)
        encoding = result['encoding'] or 'utf-8'
        logger.info(f"Detected encoding: {encoding} (confidence: {result['confidence']})")
        return encoding

    def normalize_column_names(self, columns: List[str]) -> Dict[str, str]:
        """
        Normalize column names to standard format.

        Args:
            columns: List of original column names

        Returns:
            Dict mapping original column names to normalized names
        """
        mapping = {}

        for col in columns:
            col_lower = col.strip().lower()

            # Try to match each column to a standard name
            if col in self.column_mapping.DATE_COLUMNS or col_lower in [c.lower() for c in self.column_mapping.DATE_COLUMNS]:
                mapping[col] = 'transaction_date'
            elif col in self.column_mapping.STATE_COLUMNS or col_lower in [c.lower() for c in self.column_mapping.STATE_COLUMNS]:
                mapping[col] = 'customer_state'
            elif col in self.column_mapping.AMOUNT_COLUMNS or col_lower in [c.lower() for c in self.column_mapping.AMOUNT_COLUMNS]:
                mapping[col] = 'gross_amount'
            elif col in self.column_mapping.TAX_COLUMNS or col_lower in [c.lower() for c in self.column_mapping.TAX_COLUMNS]:
                mapping[col] = 'tax_collected'
            elif col in self.column_mapping.SHIPPING_COLUMNS or col_lower in [c.lower() for c in self.column_mapping.SHIPPING_COLUMNS]:
                mapping[col] = 'shipping_amount'
            elif col in self.column_mapping.ORDER_ID_COLUMNS or col_lower in [c.lower() for c in self.column_mapping.ORDER_ID_COLUMNS]:
                mapping[col] = 'order_id'
            elif col in self.column_mapping.CUSTOMER_ID_COLUMNS or col_lower in [c.lower() for c in self.column_mapping.CUSTOMER_ID_COLUMNS]:
                mapping[col] = 'customer_id'
            elif col in self.column_mapping.MARKETPLACE_COLUMNS or col_lower in [c.lower() for c in self.column_mapping.MARKETPLACE_COLUMNS]:
                mapping[col] = 'marketplace_name'
            elif col in self.column_mapping.EXEMPT_COLUMNS or col_lower in [c.lower() for c in self.column_mapping.EXEMPT_COLUMNS]:
                mapping[col] = 'is_exempt'
            else:
                # Keep original name for unmapped columns
                mapping[col] = col.lower().replace(' ', '_')

        logger.info(f"Column mapping: {mapping}")
        return mapping

    def parse_csv(self, file_content: bytes) -> pd.DataFrame:
        """
        Parse CSV file into pandas DataFrame.

        Args:
            file_content: Raw CSV file bytes

        Returns:
            DataFrame: Parsed CSV data

        Raises:
            ValueError: If CSV parsing fails
        """
        # Detect encoding
        encoding = self.detect_encoding(file_content)

        try:
            # Try to read with detected encoding
            df = pd.read_csv(
                io.BytesIO(file_content),
                encoding=encoding,
                skipinitialspace=True
            )
        except UnicodeDecodeError:
            # Fallback to utf-8 with error handling
            logger.warning(f"Failed to decode with {encoding}, trying utf-8")
            df = pd.read_csv(
                io.BytesIO(file_content),
                encoding='utf-8',
                encoding_errors='ignore',
                skipinitialspace=True
            )

        # Normalize column names
        column_mapping = self.normalize_column_names(df.columns.tolist())
        df.rename(columns=column_mapping, inplace=True)

        logger.info(f"Parsed CSV with {len(df)} rows and columns: {df.columns.tolist()}")
        return df

    def validate_and_convert_date(self, date_value: any) -> Optional[datetime]:
        """
        Validate and convert date value.

        Args:
            date_value: Date value to validate

        Returns:
            datetime: Parsed date or None if invalid
        """
        if pd.isna(date_value):
            return None

        try:
            # Try multiple date formats
            if isinstance(date_value, str):
                date_formats = [
                    '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y',
                    '%Y/%m/%d', '%m-%d-%Y', '%d-%m-%Y'
                ]
                for fmt in date_formats:
                    try:
                        return datetime.strptime(date_value.strip(), fmt)
                    except ValueError:
                        continue
            elif isinstance(date_value, datetime):
                return date_value
            elif isinstance(date_value, pd.Timestamp):
                return date_value.to_pydatetime()

            return None
        except Exception:
            return None

    def validate_and_convert_state(self, state_value: any) -> Optional[str]:
        """
        Validate and convert state code.

        Args:
            state_value: State value to validate

        Returns:
            str: Two-letter state code or None if invalid
        """
        if pd.isna(state_value):
            return None

        state_str = str(state_value).strip().upper()

        # Check if it's already a valid state code
        if state_str in STATE_CODES:
            return state_str

        # Check if it's a full state name
        if state_str in STATE_NAMES_TO_CODES:
            return STATE_NAMES_TO_CODES[state_str]

        return None

    def validate_and_convert_amount(self, amount_value: any) -> Optional[Decimal]:
        """
        Validate and convert amount value.

        Args:
            amount_value: Amount value to validate

        Returns:
            Decimal: Parsed amount or None if invalid
        """
        if pd.isna(amount_value):
            return Decimal('0.00')

        try:
            # Remove currency symbols and commas
            if isinstance(amount_value, str):
                amount_str = amount_value.strip().replace('$', '').replace(',', '')
                return Decimal(amount_str)
            else:
                return Decimal(str(amount_value))
        except (InvalidOperation, ValueError):
            return None

    def validate_row(self, row: pd.Series, row_number: int) -> Tuple[bool, Optional[Dict]]:
        """
        Validate a single row of data.

        Args:
            row: DataFrame row
            row_number: Row number for error reporting

        Returns:
            Tuple of (is_valid, validated_data or error_dict)
        """
        errors = []

        # Validate required fields
        if 'transaction_date' not in row or pd.isna(row.get('transaction_date')):
            errors.append("Missing transaction date")

        if 'customer_state' not in row or pd.isna(row.get('customer_state')):
            errors.append("Missing customer state")

        if 'gross_amount' not in row or pd.isna(row.get('gross_amount')):
            errors.append("Missing gross amount")

        # Convert and validate date
        transaction_date = self.validate_and_convert_date(row.get('transaction_date'))
        if transaction_date is None and 'transaction_date' in row:
            errors.append("Invalid date format")

        # Convert and validate state
        customer_state = self.validate_and_convert_state(row.get('customer_state'))
        if customer_state is None and 'customer_state' in row:
            errors.append("Invalid state code")

        # Convert and validate amount
        gross_amount = self.validate_and_convert_amount(row.get('gross_amount'))
        if gross_amount is None:
            errors.append("Invalid amount")

        if errors:
            return False, {
                'row_number': row_number,
                'errors': errors,
                'data': row.to_dict()
            }

        # Build validated data
        validated_data = {
            'transaction_date': transaction_date,
            'customer_state': customer_state,
            'gross_amount': gross_amount,
            'tax_collected': self.validate_and_convert_amount(row.get('tax_collected', 0)),
            'shipping_amount': self.validate_and_convert_amount(row.get('shipping_amount', 0)),
            'order_id': str(row.get('order_id', '')).strip() if pd.notna(row.get('order_id')) else None,
            'customer_id': str(row.get('customer_id', '')).strip() if pd.notna(row.get('customer_id')) else None,
            'marketplace_name': str(row.get('marketplace_name', '')).strip() if pd.notna(row.get('marketplace_name')) else None,
            'is_marketplace_sale': bool(row.get('marketplace_name')) if 'marketplace_name' in row else False,
            'is_exempt_sale': bool(row.get('is_exempt', False)),
            'original_row_number': str(row_number)
        }

        return True, validated_data

    def process_dataframe(
        self,
        df: pd.DataFrame,
        analysis_id: str,
        db: Session
    ) -> Dict:
        """
        Process entire DataFrame with validation and batch insert.

        Args:
            df: Parsed DataFrame
            analysis_id: Analysis UUID
            db: Database session

        Returns:
            Dict with processing results
        """
        self.validation_errors = []
        self.valid_row_count = 0
        self.invalid_row_count = 0
        valid_transactions = []

        # Process each row
        for idx, row in df.iterrows():
            is_valid, result = self.validate_row(row, idx + 2)  # +2 for header row and 1-based indexing

            if is_valid:
                self.valid_row_count += 1
                # Create transaction object
                transaction = Transaction(
                    analysis_id=analysis_id,
                    **result
                )
                valid_transactions.append(transaction)
            else:
                self.invalid_row_count += 1
                self.validation_errors.append(result)

        # Calculate data quality percentage
        total_rows = len(df)
        quality_percentage = (self.valid_row_count / total_rows * 100) if total_rows > 0 else 0

        # Check if quality meets threshold (80%)
        if quality_percentage < 80:
            return {
                'success': False,
                'error': f"Data quality too low: {quality_percentage:.1f}% valid rows (minimum 80% required)",
                'valid_rows': self.valid_row_count,
                'invalid_rows': self.invalid_row_count,
                'total_rows': total_rows,
                'quality_percentage': quality_percentage,
                'validation_errors': self.validation_errors[:100]  # Limit error list
            }

        # Batch insert valid transactions
        try:
            db.bulk_save_objects(valid_transactions)
            db.commit()
            logger.info(f"Inserted {len(valid_transactions)} transactions")
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to insert transactions: {e}")
            return {
                'success': False,
                'error': f"Database error: {str(e)}",
                'valid_rows': self.valid_row_count,
                'invalid_rows': self.invalid_row_count
            }

        return {
            'success': True,
            'valid_rows': self.valid_row_count,
            'invalid_rows': self.invalid_row_count,
            'total_rows': total_rows,
            'quality_percentage': quality_percentage,
            'validation_errors': self.validation_errors[:100]  # Include some errors for reporting
        }


# Create global instance
csv_processor = CSVProcessor()

"""
Transaction model for storing sales transaction data.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Boolean, Date, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from database import Base


class Transaction(Base):
    """
    Individual sales transaction record.
    Imported from CSV files for nexus analysis.
    """
    __tablename__ = "transactions"

    transaction_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False
    )

    # Analysis relationship
    analysis_id = Column(
        UUID(as_uuid=True),
        ForeignKey("analyses.analysis_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Transaction details
    transaction_date = Column(Date, nullable=False, index=True)
    customer_state = Column(String(2), nullable=False, index=True)  # Two-letter state code

    # Amounts (stored as Numeric for precision)
    gross_amount = Column(Numeric(12, 2), nullable=False)
    tax_collected = Column(Numeric(12, 2), default=0, nullable=False)
    shipping_amount = Column(Numeric(12, 2), default=0, nullable=False)

    # Transaction type flags
    is_marketplace_sale = Column(Boolean, default=False, nullable=False, index=True)
    is_exempt_sale = Column(Boolean, default=False, nullable=False)

    # Optional fields
    customer_id = Column(String(100), nullable=True)
    order_id = Column(String(100), nullable=True, index=True)
    product_category = Column(String(100), nullable=True)
    exemption_reason = Column(String(100), nullable=True)  # Resale, Government, etc.

    # Marketplace information
    marketplace_name = Column(String(100), nullable=True, index=True)

    # Original row data (for reference)
    original_row_number = Column(String(10), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    analysis = relationship("Analysis", back_populates="transactions")

    # Composite indexes for common queries
    __table_args__ = (
        Index('ix_transactions_analysis_state', 'analysis_id', 'customer_state'),
        Index('ix_transactions_analysis_date', 'analysis_id', 'transaction_date'),
        Index('ix_transactions_state_date', 'customer_state', 'transaction_date'),
    )

    def __repr__(self):
        return f"<Transaction {self.order_id} ${self.gross_amount} to {self.customer_state}>"

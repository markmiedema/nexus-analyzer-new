"""
Tests for CSV processing functionality.
"""

import pytest
from fastapi import UploadFile
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import Mock, patch, MagicMock
import io
import pandas as pd
from datetime import datetime
from decimal import Decimal

from main import app
from database import Base, get_db
from models.user import User, UserRole
from models.tenant import Tenant
from models.analysis import Analysis, AnalysisStatus
from models.transaction import Transaction
from services.csv_processor import csv_processor
from services.auth_service import create_access_token


# In-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_tenant(db_session):
    """Create a test tenant."""
    tenant = Tenant(
        company_name="Test Company",
        subdomain="test"
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant


@pytest.fixture
def test_user(db_session, test_tenant):
    """Create a test user."""
    user = User(
        tenant_id=test_tenant.tenant_id,
        email="test@example.com",
        password_hash="hashed_password",
        first_name="Test",
        last_name="User",
        role=UserRole.ADMIN
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_token(test_user):
    """Generate auth token for test user."""
    return create_access_token({"sub": test_user.email})


@pytest.fixture
def auth_headers(auth_token):
    """Create authorization headers."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def sample_csv_content():
    """Create sample CSV content."""
    csv_data = """date,state,amount,tax_collected,shipping_amount,order_id
2024-01-15,CA,100.00,8.50,5.00,ORD-001
2024-01-16,NY,250.00,20.00,10.00,ORD-002
2024-01-17,TX,150.00,12.00,7.50,ORD-003
2024-01-18,Florida,200.00,15.00,8.00,ORD-004
"""
    return csv_data.encode('utf-8')


@pytest.fixture
def sample_csv_with_errors():
    """Create CSV with validation errors."""
    csv_data = """date,state,amount,tax_collected
2024-01-15,CA,100.00,8.50
invalid-date,NY,250.00,20.00
2024-01-17,INVALID,150.00,12.00
2024-01-18,TX,not-a-number,15.00
"""
    return csv_data.encode('utf-8')


# ==================== CSV Processor Service Tests ====================

def test_detect_encoding():
    """Test encoding detection."""
    utf8_content = "Hello, World!".encode('utf-8')
    encoding = csv_processor.detect_encoding(utf8_content)
    assert encoding in ['utf-8', 'ascii']  # ascii is subset of utf-8


def test_normalize_column_names():
    """Test column name normalization."""
    columns = ['Date', 'Customer State', 'Total', 'Sales Tax', 'Shipping']
    mapping = csv_processor.normalize_column_names(columns)

    assert mapping['Date'] == 'transaction_date'
    assert mapping['Customer State'] == 'customer_state'
    assert mapping['Total'] == 'gross_amount'
    assert mapping['Sales Tax'] == 'tax_collected'
    assert mapping['Shipping'] == 'shipping_amount'


def test_parse_csv_success(sample_csv_content):
    """Test successful CSV parsing."""
    df = csv_processor.parse_csv(sample_csv_content)

    assert len(df) == 4
    assert 'transaction_date' in df.columns
    assert 'customer_state' in df.columns
    assert 'gross_amount' in df.columns


def test_validate_and_convert_date():
    """Test date validation and conversion."""
    # Valid dates
    assert csv_processor.validate_and_convert_date('2024-01-15') == datetime(2024, 1, 15)
    assert csv_processor.validate_and_convert_date('01/15/2024') == datetime(2024, 1, 15)
    assert csv_processor.validate_and_convert_date('15/01/2024') == datetime(2024, 1, 15)

    # Invalid date
    assert csv_processor.validate_and_convert_date('invalid-date') is None
    assert csv_processor.validate_and_convert_date('') is None
    assert csv_processor.validate_and_convert_date(pd.NA) is None


def test_validate_and_convert_state():
    """Test state code validation and conversion."""
    # State abbreviations
    assert csv_processor.validate_and_convert_state('CA') == 'CA'
    assert csv_processor.validate_and_convert_state('ny') == 'NY'

    # Full state names
    assert csv_processor.validate_and_convert_state('California') == 'CA'
    assert csv_processor.validate_and_convert_state('FLORIDA') == 'FL'
    assert csv_processor.validate_and_convert_state('New York') == 'NY'

    # Invalid states
    assert csv_processor.validate_and_convert_state('INVALID') is None
    assert csv_processor.validate_and_convert_state('') is None
    assert csv_processor.validate_and_convert_state(pd.NA) is None


def test_validate_and_convert_amount():
    """Test amount validation and conversion."""
    # Valid amounts
    assert csv_processor.validate_and_convert_amount('100.00') == Decimal('100.00')
    assert csv_processor.validate_and_convert_amount('$1,234.56') == Decimal('1234.56')
    assert csv_processor.validate_and_convert_amount(250) == Decimal('250')

    # Invalid amounts
    assert csv_processor.validate_and_convert_amount('not-a-number') is None

    # Missing values default to 0.00
    assert csv_processor.validate_and_convert_amount(pd.NA) == Decimal('0.00')


def test_validate_row_success(sample_csv_content):
    """Test row validation with valid data."""
    df = csv_processor.parse_csv(sample_csv_content)
    row = df.iloc[0]

    is_valid, result = csv_processor.validate_row(row, 2)

    assert is_valid is True
    assert result['transaction_date'] == datetime(2024, 1, 15)
    assert result['customer_state'] == 'CA'
    assert result['gross_amount'] == Decimal('100.00')
    assert result['tax_collected'] == Decimal('8.50')
    assert result['shipping_amount'] == Decimal('5.00')
    assert result['order_id'] == 'ORD-001'


def test_validate_row_with_full_state_name(sample_csv_content):
    """Test row validation with full state name."""
    df = csv_processor.parse_csv(sample_csv_content)
    row = df.iloc[3]  # Florida row

    is_valid, result = csv_processor.validate_row(row, 5)

    assert is_valid is True
    assert result['customer_state'] == 'FL'  # Converted to abbreviation


def test_validate_row_with_errors(sample_csv_with_errors):
    """Test row validation with invalid data."""
    df = csv_processor.parse_csv(sample_csv_with_errors)

    # Row with invalid date
    is_valid, result = csv_processor.validate_row(df.iloc[1], 3)
    assert is_valid is False
    assert 'Invalid date format' in result['errors']

    # Row with invalid state
    is_valid, result = csv_processor.validate_row(df.iloc[2], 4)
    assert is_valid is False
    assert 'Invalid state code' in result['errors']

    # Row with invalid amount
    is_valid, result = csv_processor.validate_row(df.iloc[3], 5)
    assert is_valid is False
    assert 'Invalid amount' in result['errors']


def test_process_dataframe_success(db_session, test_user, sample_csv_content):
    """Test DataFrame processing with valid data."""
    analysis = Analysis(
        tenant_id=test_user.tenant_id,
        created_by=test_user.user_id,
        client_name="Test Client",
        period_start="2024-01-01",
        period_end="2024-12-31",
        status=AnalysisStatus.PROCESSING_CSV
    )
    db_session.add(analysis)
    db_session.commit()

    df = csv_processor.parse_csv(sample_csv_content)
    result = csv_processor.process_dataframe(df, str(analysis.analysis_id), db_session)

    assert result['success'] is True
    assert result['valid_rows'] == 4
    assert result['invalid_rows'] == 0
    assert result['quality_percentage'] == 100.0

    # Check transactions were inserted
    transactions = db_session.query(Transaction).filter(
        Transaction.analysis_id == str(analysis.analysis_id)
    ).all()
    assert len(transactions) == 4


def test_process_dataframe_low_quality(db_session, test_user):
    """Test DataFrame processing with low data quality."""
    analysis = Analysis(
        tenant_id=test_user.tenant_id,
        created_by=test_user.user_id,
        client_name="Test Client",
        period_start="2024-01-01",
        period_end="2024-12-31",
        status=AnalysisStatus.PROCESSING_CSV
    )
    db_session.add(analysis)
    db_session.commit()

    # Create CSV with mostly invalid data (only 1 valid row out of 10)
    csv_data = """date,state,amount
2024-01-15,CA,100.00
invalid,NY,250
invalid,TX,150
invalid,FL,200
invalid,GA,300
invalid,IL,400
invalid,PA,500
invalid,OH,600
invalid,MI,700
invalid,WA,800
"""
    df = csv_processor.parse_csv(csv_data.encode('utf-8'))
    result = csv_processor.process_dataframe(df, str(analysis.analysis_id), db_session)

    assert result['success'] is False
    assert result['quality_percentage'] < 80
    assert 'Data quality too low' in result['error']


# ==================== CSV Upload API Tests ====================

@patch('api.csv_processor.s3_service')
@patch('api.csv_processor.process_csv_file')
def test_upload_csv_success(mock_celery_task, mock_s3, client, auth_headers, test_user, sample_csv_content):
    """Test successful CSV file upload."""
    # Mock S3 upload
    mock_s3.upload_file.return_value = "test/path/file.csv"
    mock_s3.build_object_key.return_value = "test/path/file.csv"

    # Mock Celery task
    mock_task = Mock()
    mock_task.id = "task-123"
    mock_celery_task.delay.return_value = mock_task

    # Create file upload
    files = {
        'file': ('test.csv', io.BytesIO(sample_csv_content), 'text/csv')
    }
    data = {
        'client_name': 'Test Client',
        'period_start': '2024-01-01',
        'period_end': '2024-12-31'
    }

    response = client.post(
        "/api/v1/csv/upload",
        files=files,
        data=data,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert 'analysis_id' in data
    assert 'task_id' in data
    assert data['status'] == 'queued'


def test_upload_csv_invalid_extension(client, auth_headers):
    """Test CSV upload with invalid file extension."""
    invalid_content = b"fake content"
    files = {
        'file': ('test.txt', io.BytesIO(invalid_content), 'text/plain')
    }
    data = {
        'client_name': 'Test Client',
        'period_start': '2024-01-01',
        'period_end': '2024-12-31'
    }

    response = client.post(
        "/api/v1/csv/upload",
        files=files,
        data=data,
        headers=auth_headers
    )

    assert response.status_code == 400
    assert 'File type not allowed' in response.json()['detail']


def test_upload_csv_file_too_large(client, auth_headers):
    """Test CSV upload with file too large."""
    # Create a file larger than MAX_FILE_SIZE
    large_content = b"x" * (100 * 1024 * 1024 + 1)  # 100MB + 1 byte
    files = {
        'file': ('test.csv', io.BytesIO(large_content), 'text/csv')
    }
    data = {
        'client_name': 'Test Client',
        'period_start': '2024-01-01',
        'period_end': '2024-12-31'
    }

    response = client.post(
        "/api/v1/csv/upload",
        files=files,
        data=data,
        headers=auth_headers
    )

    assert response.status_code == 413
    assert 'File too large' in response.json()['detail']


def test_upload_csv_empty_file(client, auth_headers):
    """Test CSV upload with empty file."""
    files = {
        'file': ('test.csv', io.BytesIO(b''), 'text/csv')
    }
    data = {
        'client_name': 'Test Client',
        'period_start': '2024-01-01',
        'period_end': '2024-12-31'
    }

    response = client.post(
        "/api/v1/csv/upload",
        files=files,
        data=data,
        headers=auth_headers
    )

    assert response.status_code == 400
    assert 'File is empty' in response.json()['detail']


def test_upload_csv_missing_filename(client, auth_headers):
    """Test CSV upload with missing filename."""
    files = {
        'file': (None, io.BytesIO(b"test"), 'text/csv')
    }
    data = {
        'client_name': 'Test Client',
        'period_start': '2024-01-01',
        'period_end': '2024-12-31'
    }

    response = client.post(
        "/api/v1/csv/upload",
        files=files,
        data=data,
        headers=auth_headers
    )

    assert response.status_code == 400
    assert 'Filename is required' in response.json()['detail']


def test_upload_csv_unauthorized(client, sample_csv_content):
    """Test CSV upload without authentication."""
    files = {
        'file': ('test.csv', io.BytesIO(sample_csv_content), 'text/csv')
    }
    data = {
        'client_name': 'Test Client',
        'period_start': '2024-01-01',
        'period_end': '2024-12-31'
    }

    response = client.post(
        "/api/v1/csv/upload",
        files=files,
        data=data
    )

    assert response.status_code == 401


# ==================== Status and Report API Tests ====================

def test_get_processing_status(client, auth_headers, test_user, db_session):
    """Test get processing status endpoint."""
    analysis = Analysis(
        tenant_id=test_user.tenant_id,
        created_by=test_user.user_id,
        client_name="Test Client",
        period_start="2024-01-01",
        period_end="2024-12-31",
        status=AnalysisStatus.PROCESSING_CSV
    )
    db_session.add(analysis)
    db_session.commit()

    response = client.get(
        f"/api/v1/csv/status/{analysis.analysis_id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data['analysis_id'] == str(analysis.analysis_id)
    assert data['status'] == 'processing_csv'
    assert data['client_name'] == 'Test Client'
    assert data['transaction_count'] == 0


def test_get_processing_status_not_found(client, auth_headers):
    """Test get processing status for non-existent analysis."""
    response = client.get(
        "/api/v1/csv/status/00000000-0000-0000-0000-000000000000",
        headers=auth_headers
    )

    assert response.status_code == 404


@patch('api.csv_processor.s3_service')
def test_get_validation_report(mock_s3, client, auth_headers, test_user, db_session):
    """Test get validation report endpoint."""
    analysis = Analysis(
        tenant_id=test_user.tenant_id,
        created_by=test_user.user_id,
        client_name="Test Client",
        period_start="2024-01-01",
        period_end="2024-12-31",
        status=AnalysisStatus.COMPLETED,
        validation_report_path="test/path/report.json"
    )
    db_session.add(analysis)
    db_session.commit()

    # Mock S3 download
    mock_report = {
        'summary': {
            'total_rows': 100,
            'valid_rows': 95,
            'invalid_rows': 5,
            'quality_percentage': 95.0
        },
        'validation_errors': []
    }
    import json
    mock_s3.download_file.return_value = json.dumps(mock_report).encode('utf-8')

    response = client.get(
        f"/api/v1/csv/validation-report/{analysis.analysis_id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data['summary']['total_rows'] == 100
    assert data['summary']['valid_rows'] == 95


def test_get_validation_report_not_available(client, auth_headers, test_user, db_session):
    """Test get validation report when not available."""
    analysis = Analysis(
        tenant_id=test_user.tenant_id,
        created_by=test_user.user_id,
        client_name="Test Client",
        period_start="2024-01-01",
        period_end="2024-12-31",
        status=AnalysisStatus.PROCESSING_CSV,
        validation_report_path=None
    )
    db_session.add(analysis)
    db_session.commit()

    response = client.get(
        f"/api/v1/csv/validation-report/{analysis.analysis_id}",
        headers=auth_headers
    )

    assert response.status_code == 404
    assert 'Validation report not available' in response.json()['detail']


# ==================== Template Download Test ====================

def test_download_csv_template(client):
    """Test CSV template download endpoint."""
    response = client.get("/api/v1/csv/templates/download")

    assert response.status_code == 200
    assert response.headers['content-type'] == 'text/csv; charset=utf-8'
    assert 'attachment' in response.headers['content-disposition']
    assert 'nexus_analyzer_template.csv' in response.headers['content-disposition']

    # Check content
    content = response.content.decode('utf-8')
    assert 'date,state,amount' in content
    assert '2024-01-15,CA,100.00' in content

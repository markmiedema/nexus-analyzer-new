# Nexus Analyzer Backend

FastAPI-based backend for the Nexus Analyzer sales tax nexus determination platform.

## Tech Stack

- **Framework**: FastAPI 0.115.0
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Async Tasks**: Celery with Redis
- **Authentication**: JWT tokens with bcrypt
- **Data Processing**: Pandas
- **PDF Generation**: WeasyPrint
- **Testing**: Pytest

## Setup

### Prerequisites

- Python 3.11 or higher
- PostgreSQL 15+
- Redis 7+

### Installation

#### Windows

```bash
# Run the setup script
setup.bat

# Or manually:
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

#### Unix/Mac/Linux

```bash
# Run the setup script
chmod +x setup.sh
./setup.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Environment Variables

Copy `.env.example` from the project root and configure:

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/nexus_analyzer
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-secret-key-here
S3_ENDPOINT_URL=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
```

## Development

### Running the Server

```bash
# Activate virtual environment first
source venv/bin/activate  # Unix/Mac
# OR
venv\Scripts\activate  # Windows

# Run development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Running Tests

```bash
pytest
# With coverage
pytest --cov=. --cov-report=html
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Run migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Code Formatting

```bash
# Format code
black .

# Lint
flake8 .

# Type checking
mypy .
```

## Project Structure

```
backend/
├── models/         # SQLAlchemy database models
├── api/            # FastAPI route handlers
├── services/       # Business logic services
├── workers/        # Celery background tasks
├── tests/          # Test files
├── main.py         # FastAPI application entry point
├── config.py       # Configuration management
├── database.py     # Database connection setup
└── requirements.txt
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## License

Proprietary - All rights reserved

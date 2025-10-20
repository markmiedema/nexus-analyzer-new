# Nexus Analyzer

A comprehensive sales tax nexus determination platform that helps businesses identify their tax obligations across all U.S. states.

## Overview

Nexus Analyzer automates the complex process of determining sales tax nexus by analyzing transaction data, physical presence, and economic thresholds. The platform provides actionable insights, liability estimates, and professional reports to guide compliance decisions.

### Key Features

- **Automated Nexus Determination**: Analyzes physical and economic nexus across all 50 states
- **CSV Upload & Processing**: Bulk transaction data import with intelligent parsing
- **Liability Estimation**: Calculates potential tax liability with lookback periods
- **Professional Reports**: Generate PDF reports with executive summaries and detailed analysis
- **Multi-Tenant Architecture**: Support for multiple clients with data isolation
- **Background Processing**: Async processing for large datasets using Celery
- **State Tax Rules Engine**: Up-to-date nexus thresholds and tax rates

## Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15+
- **ORM**: SQLAlchemy with Alembic migrations
- **Cache/Queue**: Redis 7+
- **Task Queue**: Celery
- **File Storage**: MinIO (S3-compatible)
- **PDF Generation**: WeasyPrint

### Frontend
- **Framework**: Next.js 15 with React 19
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: React Query
- **Forms**: React Hook Form + Zod

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Orchestration**: Docker Compose (development), Kubernetes (production ready)

## Project Structure

```
nexus-analyzer/
├── backend/                # Python FastAPI backend
│   ├── alembic/           # Database migrations
│   ├── api/               # API route handlers
│   ├── models/            # SQLAlchemy models
│   ├── services/          # Business logic
│   ├── workers/           # Celery background tasks
│   ├── config.py          # Configuration management
│   ├── database.py        # Database setup
│   ├── main.py            # FastAPI entry point
│   ├── requirements.txt   # Python dependencies
│   └── Dockerfile         # Backend container
├── frontend/              # Next.js frontend
│   ├── app/               # Next.js app directory
│   ├── components/        # React components
│   ├── package.json       # Node dependencies
│   └── Dockerfile         # Frontend container
├── tasks/                 # Project task lists
├── docker-compose.yml     # Docker services configuration
├── .env.example           # Environment variables template
└── README.md              # This file
```

## Getting Started

### Prerequisites

- **Docker Desktop** (Windows/Mac) or **Docker Engine + Docker Compose** (Linux)
- **Git** for version control
- **Node.js 20+** (for local frontend development)
- **Python 3.11+** (for local backend development)

### Quick Start with Docker Compose

1. **Clone the repository**

```bash
git clone <repository-url>
cd nexus-analyzer
```

2. **Create environment file**

```bash
# Copy the example environment file
copy .env.example .env  # Windows
# OR
cp .env.example .env    # Linux/Mac

# Edit .env and update values as needed
# At minimum, change SECRET_KEY and database passwords
```

3. **Start all services**

```bash
# Build and start all containers
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build
```

4. **Access the application**

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9001 (admin/minioadmin)

5. **Run database migrations**

```bash
# Run migrations to create database schema
docker-compose exec backend alembic upgrade head
```

### Development Setup (Local)

#### Backend Development

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Copy .env file to backend directory
copy ..\.env .env  # Windows
cp ../.env .env    # Linux/Mac

# Run migrations
alembic upgrade head

# Start development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## Docker Compose Services

The application consists of the following services:

| Service | Port | Description |
|---------|------|-------------|
| **postgres** | 5432 | PostgreSQL database |
| **redis** | 6379 | Redis cache and task queue |
| **minio** | 9000, 9001 | S3-compatible object storage |
| **backend** | 8000 | FastAPI backend API |
| **celery-worker** | - | Background task processor |
| **frontend** | 3000 | Next.js web application |

### Useful Docker Commands

```bash
# View logs
docker-compose logs -f [service-name]

# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes all data)
docker-compose down -v

# Restart a specific service
docker-compose restart [service-name]

# Execute command in container
docker-compose exec backend bash
docker-compose exec frontend sh

# View running containers
docker-compose ps

# Rebuild specific service
docker-compose up -d --build backend
```

## Database Migrations

```bash
# Create a new migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec backend alembic upgrade head

# Rollback one migration
docker-compose exec backend alembic downgrade -1

# View migration history
docker-compose exec backend alembic history

# View current version
docker-compose exec backend alembic current
```

## Testing

### Backend Tests

```bash
# Run all tests
docker-compose exec backend pytest

# Run with coverage
docker-compose exec backend pytest --cov=. --cov-report=html

# Run specific test file
docker-compose exec backend pytest tests/test_auth.py
```

### Frontend Tests

```bash
# Run tests
docker-compose exec frontend npm test

# Run tests in watch mode
docker-compose exec frontend npm test -- --watch
```

## Environment Variables

See `.env.example` for all available configuration options. Key variables:

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: JWT signing key (generate with `openssl rand -hex 32`)
- `S3_*`: MinIO/S3 configuration
- `NEXT_PUBLIC_API_URL`: Backend API URL (accessible from browser)

## API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Roadmap

See `tasks/tasks-nexus-analyzer-phase1-mvp.md` for the complete Phase 1 MVP task list.

### Completed
- ✅ Project infrastructure setup
- ✅ Frontend Next.js initialization
- ✅ Docker Compose configuration
- ✅ Alembic database migrations setup

### In Progress
- 🔄 Database models and schema
- 🔄 Authentication and multi-tenancy
- 🔄 CSV upload and processing

### Upcoming
- ⏳ Nexus rules engine
- ⏳ Liability estimation
- ⏳ Report generation
- ⏳ Frontend UI components

## Contributing

This is a private project. For questions or issues, contact the development team.

## License

Proprietary - All rights reserved

## Support

For issues or questions:
- Check the documentation in `/docs`
- Review existing issues
- Contact: [your-email@example.com]

---

**Version**: 0.1.0 (MVP Phase 1)
**Last Updated**: October 2025

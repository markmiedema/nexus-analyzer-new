# Getting Started - Nexus Analyzer

This guide will help you get the Nexus Analyzer application up and running on your local machine.

## Prerequisites

- Docker Desktop installed and running
- Node.js 18+ and npm installed
- Python 3.11+ (if running backend locally without Docker)

## Quick Start (Recommended)

### 1. Set Up Environment Files

**Backend:**
```bash
cd backend
copy .env.example .env
```

**Frontend:**
```bash
cd frontend
copy .env.example .env
```

### 2. Start Backend Services with Docker

From the root directory:

```bash
docker-compose up -d
```

This will start:
- PostgreSQL database (port 5432)
- Redis (port 6379)
- MinIO (port 9000, console: 9001)
- FastAPI backend (port 8000)
- Celery worker

**Note:** First startup will take a few minutes to build images and initialize databases.

### 3. Initialize Database

Wait for services to start (about 30 seconds), then run migrations:

```bash
docker-compose exec backend alembic upgrade head
```

### 4. Create Initial Tenant and User

Run the seed script to create a demo tenant and user:

```bash
docker-compose exec backend python seeds/create_demo_user.py
```

This creates:
- **Email:** demo@nexusanalyzer.com
- **Password:** demo123
- **Tenant:** Demo Company

### 5. Start Frontend Development Server

In a new terminal:

```bash
cd frontend
npm install  # If you haven't already
npm run dev
```

The frontend will be available at: **http://localhost:3000**

### 6. Access the Application

1. Open your browser to http://localhost:3000
2. You'll be redirected to the login page
3. Log in with:
   - **Email:** demo@nexusanalyzer.com
   - **Password:** demo123

## Service URLs

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs (Swagger UI)
- **MinIO Console:** http://localhost:9001 (admin/minioadmin)

## Verify Everything is Running

### Check Backend Status

```bash
curl http://localhost:8000/health
```

Should return: `{"status":"healthy","version":"0.1.0"}`

### Check Database Connection

```bash
docker-compose exec backend python -c "from database import engine; print('DB Connected!' if engine else 'Failed')"
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f celery-worker
```

## Stopping the Application

### Stop all services:
```bash
docker-compose down
```

### Stop and remove all data (reset):
```bash
docker-compose down -v
```

## Troubleshooting

### Backend won't start
- Check Docker Desktop is running
- Verify ports 8000, 5432, 6379, 9000 are not in use
- Check logs: `docker-compose logs backend`

### Database migration errors
```bash
# Reset database
docker-compose down -v
docker-compose up -d
docker-compose exec backend alembic upgrade head
```

### Frontend can't connect to backend
- Verify backend is running: http://localhost:8000/health
- Check NEXT_PUBLIC_API_URL in frontend/.env is set to http://localhost:8000
- Check CORS_ORIGINS in backend/.env includes http://localhost:3000

### Celery worker not processing tasks
```bash
# Check worker logs
docker-compose logs -f celery-worker

# Restart worker
docker-compose restart celery-worker
```

## Development Workflow

### Running Tests (when implemented)
```bash
# Backend tests
docker-compose exec backend pytest

# Frontend tests
cd frontend && npm test
```

### Accessing the Database
```bash
docker-compose exec postgres psql -U nexus_admin -d nexus_analyzer
```

### Rebuilding After Code Changes

**Backend:**
```bash
docker-compose up -d --build backend
```

**Frontend:**
```bash
# Frontend auto-reloads with npm run dev
# No rebuild needed during development
```

## Next Steps

1. Create a new analysis from the dashboard
2. Upload a CSV file with transaction data
3. Fill in the business profile
4. Wait for analysis to complete
5. View nexus results and liability estimates
6. Generate and download PDF reports

## Sample CSV Format

Create a CSV file with these columns:

```csv
transaction_date,state,amount,transaction_id,is_exempt
2024-01-15,CA,150.00,TXN001,false
2024-01-16,NY,200.00,TXN002,false
2024-01-17,TX,175.00,TXN003,true
```

Required columns:
- `transaction_date` (YYYY-MM-DD or MM/DD/YYYY)
- `state` (2-letter state code)
- `amount` (decimal)

Optional columns:
- `transaction_id` (string)
- `is_exempt` (true/false)
- `is_marketplace` (true/false)
- `product_category` (string)

## Need Help?

- Check the API documentation: http://localhost:8000/docs
- Review logs: `docker-compose logs -f`
- See tasks/tasks-nexus-analyzer-phase1-mvp.md for implementation details

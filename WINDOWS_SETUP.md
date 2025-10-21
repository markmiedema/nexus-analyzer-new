# Windows Setup Guide for Nexus Analyzer

This guide will help you set up and run Nexus Analyzer on Windows using Docker Desktop.

## Prerequisites

- **Windows 10/11** (64-bit)
- **Docker Desktop** installed and running
- **PowerShell 5.1+** (comes with Windows)
- **At least 4GB RAM** available for Docker

## Quick Start (Recommended)

### Step 1: Ensure Docker Desktop is Running

1. Look for the Docker whale icon (🐋) in your system tray
2. If not running, start **Docker Desktop**
3. Wait 60 seconds for Docker to fully initialize

### Step 2: Navigate to Your Project

Open PowerShell and navigate to your project directory:

```powershell
cd C:\Users\markw\nexus-analyzer-new\nexus-analyzer-new
```

### Step 3: Allow PowerShell Scripts (First Time Only)

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

When prompted, type `Y` to confirm.

### Step 4: Run the Quick Start Script

```powershell
.\quick-start.ps1
```

The script will:
- ✅ Check if Docker is running
- ✅ Create `.env` file if needed
- ✅ Provide an easy menu to manage services

### Step 5: Choose Option 1 to Start

Select option **1** from the menu to start all services.

Wait 30-60 seconds for services to initialize, then access:
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000/docs
- **MinIO Console:** http://localhost:9001

## Troubleshooting with Diagnostic Script

If you encounter issues, run the diagnostic script:

```powershell
.\diagnose-nexus.ps1
```

This will check:
- ✅ Docker installation and connectivity
- ✅ Required project files
- ✅ Port availability
- ✅ Environment configuration
- ✅ Container status
- ✅ System resources

## Manual Setup (Alternative)

If you prefer to run commands manually:

### 1. Create Environment File

```powershell
# Copy example file
Copy-Item .env.example .env

# Open for editing
notepad .env
```

### 2. Generate a Secure SECRET_KEY

In PowerShell:
```powershell
-join ((1..32) | ForEach-Object { '{0:x2}' -f (Get-Random -Maximum 256) })
```

Copy the output and paste it as your `SECRET_KEY` in `.env`

### 3. Start Services

```powershell
docker compose up -d
```

### 4. Check Status

```powershell
docker compose ps
```

### 5. View Logs

```powershell
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
```

### 6. Stop Services

```powershell
docker compose down
```

## Common Issues and Solutions

### Issue: "Docker not found"

**Solution:**
1. Install Docker Desktop from: https://www.docker.com/products/docker-desktop
2. Restart your computer
3. Start Docker Desktop and wait for it to initialize

### Issue: "Cannot connect to Docker daemon"

**Solution:**
1. Make sure Docker Desktop is running (check system tray for 🐋)
2. Wait 60 seconds after starting Docker Desktop
3. In Docker Desktop settings, ensure WSL 2 is enabled (if using WSL)

### Issue: "Port already in use"

**Solution:**

Check which ports are in use:
```powershell
Get-NetTCPConnection -LocalPort 3000,8000,5432,6379,9000,9001 -ErrorAction SilentlyContinue
```

Option 1: Stop the conflicting application

Option 2: Change ports in `.env` file:
```
FRONTEND_PORT=3001
BACKEND_PORT=8001
# etc.
```

### Issue: "Services start but frontend/backend won't load"

**Solution:**

1. Check if services are healthy:
   ```powershell
   docker compose ps
   ```

2. View logs to see errors:
   ```powershell
   docker compose logs -f backend
   docker compose logs -f frontend
   ```

3. Common fixes:
   - Restart services: `docker compose restart`
   - Fresh start: `docker compose down -v && docker compose up -d`

### Issue: "Path too long" errors

Your current path has a duplicate folder:
```
C:\Users\markw\nexus-analyzer-new\nexus-analyzer-new
```

**Solution:** Simplify the path (optional):

```powershell
# Option 1: Move contents up one level
cd C:\Users\markw\nexus-analyzer-new
Move-Item nexus-analyzer-new\* . -Force
Remove-Item nexus-analyzer-new

# New path: C:\Users\markw\nexus-analyzer-new
```

### Issue: "SECRET_KEY is using default value"

**Solution:**

Generate a secure key:
```powershell
# PowerShell command
-join ((1..32) | ForEach-Object { '{0:x2}' -f (Get-Random -Maximum 256) })
```

Or use OpenSSL (if installed):
```powershell
openssl rand -hex 32
```

Update the `SECRET_KEY` in your `.env` file.

## Project Structure

```
nexus-analyzer-new/
├── backend/                 # Python FastAPI backend
│   ├── Dockerfile
│   ├── requirements.txt
│   └── ...
├── frontend/               # Next.js frontend
│   ├── Dockerfile
│   ├── package.json
│   └── ...
├── docker-compose.yml      # Docker orchestration
├── .env.example           # Environment template
├── .env                   # Your environment (create this)
├── diagnose-nexus.ps1     # Diagnostic tool
├── quick-start.ps1        # Quick start menu
└── WINDOWS_SETUP.md       # This file
```

## Services Overview

When you run `docker compose up -d`, these services start:

| Service | Port | Description |
|---------|------|-------------|
| **Frontend** | 3000 | Next.js web interface |
| **Backend** | 8000 | FastAPI REST API |
| **PostgreSQL** | 5432 | Database |
| **Redis** | 6379 | Cache & queue |
| **MinIO** | 9000 | S3-compatible storage |
| **MinIO Console** | 9001 | MinIO admin interface |
| **Celery Worker** | - | Background task processor |

## Useful Commands Reference

### Service Management
```powershell
# Start all services
docker compose up -d

# Stop all services
docker compose down

# Restart all services
docker compose restart

# Stop and remove all data (fresh start)
docker compose down -v
```

### Monitoring
```powershell
# View status of all containers
docker compose ps

# View logs (all services)
docker compose logs -f

# View logs (specific service)
docker compose logs -f backend

# View last 50 log lines
docker compose logs --tail=50
```

### Cleanup
```powershell
# Remove containers and volumes
docker compose down -v

# Remove all unused Docker resources
docker system prune -a

# Remove specific volume
docker volume rm nexus-analyzer-new_postgres_data
```

### Executing Commands in Containers
```powershell
# Access backend shell
docker compose exec backend bash

# Run database migrations
docker compose exec backend alembic upgrade head

# Access database
docker compose exec postgres psql -U nexus_admin -d nexus_analyzer
```

## Development Workflow

### Making Code Changes

The project uses Docker volumes for hot-reloading:
- **Backend:** Changes to Python files auto-reload
- **Frontend:** Changes to React/Next.js files auto-reload

No need to rebuild containers for code changes!

### Rebuilding After Dependency Changes

If you modify `requirements.txt` or `package.json`:

```powershell
# Rebuild and restart
docker compose up -d --build
```

### Viewing API Documentation

Backend provides interactive API docs:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Next Steps

1. ✅ Start services with `.\quick-start.ps1`
2. ✅ Access frontend at http://localhost:3000
3. ✅ Check API docs at http://localhost:8000/docs
4. ✅ Review logs if issues occur
5. ✅ Read main README.md for application usage

## Need Help?

1. Run `.\diagnose-nexus.ps1` for automated troubleshooting
2. Check logs with `docker compose logs -f`
3. Review [Docker Desktop documentation](https://docs.docker.com/desktop/windows/)
4. Check the main [README.md](README.md) for project details

## Security Notes

- **Never commit `.env` to version control**
- Change all default passwords in `.env`
- Generate a strong `SECRET_KEY`
- Use environment-specific `.env` files for production

## Performance Tips

1. **Allocate sufficient resources** in Docker Desktop settings:
   - Memory: 4GB minimum, 8GB recommended
   - CPUs: 2 minimum, 4 recommended

2. **Enable WSL 2** backend for better performance (Windows 10/11)

3. **Exclude project folder** from Windows Defender real-time scanning

4. **Use SSD** for Docker storage location

---

**Ready to start?** Run `.\quick-start.ps1` and select option 1! 🚀

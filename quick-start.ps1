# Nexus Analyzer Quick Start Script
# Easy menu-driven script to manage Docker containers
# Run this from your project directory

$ErrorActionPreference = "Stop"

function Write-Step { param($msg) Write-Host "`n▶ $msg" -ForegroundColor Cyan }
function Write-Success { param($msg) Write-Host "  ✓ $msg" -ForegroundColor Green }
function Write-Fail { param($msg) Write-Host "  ✗ $msg" -ForegroundColor Red }
function Write-Info { param($msg) Write-Host "  ℹ $msg" -ForegroundColor Yellow }

Write-Host @"

╔════════════════════════════════════════╗
║   Nexus Analyzer - Quick Start        ║
║   Docker Management Tool               ║
╚════════════════════════════════════════╝

"@ -ForegroundColor Green

# Get current directory
$currentDir = Get-Location
Write-Info "Current directory: $currentDir"

# Pre-flight checks
Write-Step "Running pre-flight checks..."

# Check if in correct directory
if (-not (Test-Path "docker-compose.yml")) {
    Write-Fail "docker-compose.yml not found in current directory!"
    Write-Info "Make sure you're in the nexus-analyzer-new directory"
    Write-Info "Expected: C:\Users\markw\nexus-analyzer-new\nexus-analyzer-new"
    exit 1
}
Write-Success "Found docker-compose.yml"

# Check Docker
try {
    docker ps 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker not responding"
    }
    Write-Success "Docker Desktop is running"
} catch {
    Write-Fail "Docker Desktop is NOT running"
    Write-Info "Please start Docker Desktop, wait 60 seconds, then run this script again"
    Write-Info "Look for the whale icon 🐋 in your system tray"
    exit 1
}

# Check .env file
if (-not (Test-Path ".env")) {
    Write-Info ".env file not found"

    if (Test-Path ".env.example") {
        Write-Step "Creating .env from template..."
        Copy-Item .env.example .env
        Write-Success ".env created successfully"

        Write-Host "`n⚠ IMPORTANT: Configure your environment" -ForegroundColor Yellow
        Write-Info "Opening .env file for editing..."
        Write-Info "Please set these important values:"
        Write-Host "   1. SECRET_KEY - Generate with: -join ((1..32) | ForEach-Object { '{0:x2}' -f (Get-Random -Maximum 256) })" -ForegroundColor Cyan
        Write-Host "   2. POSTGRES_PASSWORD - Change from default" -ForegroundColor Cyan
        Write-Host "   3. MINIO_ROOT_PASSWORD - Change from default" -ForegroundColor Cyan

        notepad .env

        Write-Host "`nPress Enter when you've finished editing .env" -ForegroundColor Yellow
        Read-Host

    } else {
        Write-Fail ".env.example not found"
        Write-Info "Cannot create .env file automatically"
        exit 1
    }
} else {
    Write-Success ".env file exists"

    # Check if using default SECRET_KEY
    $envContent = Get-Content .env
    $secretKey = $envContent | Select-String "^SECRET_KEY="
    if ($secretKey -and $secretKey -match "your-secret-key|change-in-production") {
        Write-Host "`n⚠ WARNING: SECRET_KEY appears to be using default value!" -ForegroundColor Red
        Write-Info "Generate secure key with: -join ((1..32) | ForEach-Object { '{0:x2}' -f (Get-Random -Maximum 256) })"
        $updateEnv = Read-Host "Open .env to update? (y/n)"
        if ($updateEnv -eq "y") {
            notepad .env
        }
    }
}

# Main menu
function Show-Menu {
    Write-Host "`n╔════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║         MAIN MENU                      ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  1. 🚀 Start all services (normal start)" -ForegroundColor White
    Write-Host "  2. 🔄 Restart services" -ForegroundColor White
    Write-Host "  3. 🆕 Fresh start (removes all data)" -ForegroundColor White
    Write-Host "  4. 🛑 Stop all services" -ForegroundColor White
    Write-Host "  5. 📊 View status" -ForegroundColor White
    Write-Host "  6. 📋 View logs" -ForegroundColor White
    Write-Host "  7. 🔍 Run diagnostic" -ForegroundColor White
    Write-Host "  8. 🧹 Clean up (remove containers, images, volumes)" -ForegroundColor White
    Write-Host "  9. ❌ Exit" -ForegroundColor White
    Write-Host ""
}

function Start-Services {
    Write-Step "Starting all services..."

    docker compose up -d

    if ($LASTEXITCODE -eq 0) {
        Write-Success "Services started successfully!"

        Write-Host "`nWaiting for services to initialize..." -ForegroundColor Gray
        Start-Sleep -Seconds 10

        Write-Step "Service Status:"
        docker compose ps

        Write-Host "`n╔════════════════════════════════════════╗" -ForegroundColor Green
        Write-Host "║   Services are running!                ║" -ForegroundColor Green
        Write-Host "╚════════════════════════════════════════╝" -ForegroundColor Green

        Write-Host "`n📱 Access your application:" -ForegroundColor Yellow
        Write-Host "   Frontend:     http://localhost:3000" -ForegroundColor Cyan
        Write-Host "   Backend API:  http://localhost:8000/docs" -ForegroundColor Cyan
        Write-Host "   MinIO Admin:  http://localhost:9001" -ForegroundColor Cyan

        Write-Host "`n💡 Tips:" -ForegroundColor Yellow
        Write-Host "   - View logs:      docker compose logs -f" -ForegroundColor Gray
        Write-Host "   - Stop services:  docker compose down" -ForegroundColor Gray
        Write-Host "   - Backend logs:   docker compose logs -f backend" -ForegroundColor Gray

    } else {
        Write-Fail "Failed to start services"
        Write-Info "Check logs with: docker compose logs"

        $viewLogs = Read-Host "`nView logs now? (y/n)"
        if ($viewLogs -eq "y") {
            docker compose logs --tail=50
        }
    }
}

function Restart-Services {
    Write-Step "Restarting services..."

    docker compose restart

    if ($LASTEXITCODE -eq 0) {
        Write-Success "Services restarted successfully!"
        Start-Sleep -Seconds 5
        docker compose ps
    } else {
        Write-Fail "Failed to restart services"
    }
}

function Start-Fresh {
    Write-Host "`n⚠ WARNING: This will DELETE all data!" -ForegroundColor Red
    Write-Host "   - All database records will be lost" -ForegroundColor Yellow
    Write-Host "   - All uploaded files will be deleted" -ForegroundColor Yellow
    Write-Host "   - Redis cache will be cleared" -ForegroundColor Yellow

    $confirm = Read-Host "`nType 'yes' to confirm fresh start"

    if ($confirm -eq "yes") {
        Write-Step "Stopping and removing containers, volumes..."
        docker compose down -v

        if ($LASTEXITCODE -eq 0) {
            Write-Success "Old data removed"

            Write-Step "Starting services fresh..."
            docker compose up -d

            if ($LASTEXITCODE -eq 0) {
                Write-Success "Services started fresh!"
                Write-Host "`nWaiting for initialization..." -ForegroundColor Gray
                Start-Sleep -Seconds 15
                docker compose ps

                Write-Host "`n✨ Fresh environment ready!" -ForegroundColor Green
                Write-Host "   Frontend: http://localhost:3000" -ForegroundColor Cyan
                Write-Host "   Backend:  http://localhost:8000/docs" -ForegroundColor Cyan
            } else {
                Write-Fail "Failed to start services"
            }
        } else {
            Write-Fail "Failed to clean up"
        }
    } else {
        Write-Info "Fresh start cancelled"
    }
}

function Stop-Services {
    Write-Step "Stopping all services..."

    docker compose down

    if ($LASTEXITCODE -eq 0) {
        Write-Success "All services stopped"
    } else {
        Write-Fail "Failed to stop services"
    }
}

function Show-Status {
    Write-Step "Current Status:"
    Write-Host ""

    docker compose ps

    Write-Host "`nDocker Resources:" -ForegroundColor Yellow
    Write-Host "Images:" -ForegroundColor Gray
    docker images | Select-String "nexus" | ForEach-Object { Write-Host "  $_" }

    Write-Host "`nVolumes:" -ForegroundColor Gray
    docker volume ls | Select-String "nexus" | ForEach-Object { Write-Host "  $_" }
}

function Show-Logs {
    Write-Step "Which service logs would you like to view?"
    Write-Host "  1. All services"
    Write-Host "  2. Backend only"
    Write-Host "  3. Frontend only"
    Write-Host "  4. PostgreSQL"
    Write-Host "  5. Redis"
    Write-Host "  6. MinIO"
    Write-Host "  7. Celery Worker"

    $logChoice = Read-Host "`nEnter choice (1-7)"

    Write-Host "`nShowing logs (press Ctrl+C to exit)..." -ForegroundColor Yellow
    Write-Host ""

    switch ($logChoice) {
        "1" { docker compose logs -f }
        "2" { docker compose logs -f backend }
        "3" { docker compose logs -f frontend }
        "4" { docker compose logs -f postgres }
        "5" { docker compose logs -f redis }
        "6" { docker compose logs -f minio }
        "7" { docker compose logs -f celery-worker }
        default {
            Write-Info "Invalid choice, showing all logs"
            docker compose logs -f
        }
    }
}

function Run-Diagnostic {
    if (Test-Path "diagnose-nexus.ps1") {
        Write-Step "Running diagnostic script..."
        & ".\diagnose-nexus.ps1"
    } else {
        Write-Fail "Diagnostic script (diagnose-nexus.ps1) not found"
        Write-Info "Make sure diagnose-nexus.ps1 is in the same directory"
    }
}

function Clean-Up {
    Write-Host "`n⚠ WARNING: This will remove:" -ForegroundColor Red
    Write-Host "   - All Nexus Analyzer containers" -ForegroundColor Yellow
    Write-Host "   - All Nexus Analyzer images" -ForegroundColor Yellow
    Write-Host "   - All Nexus Analyzer volumes (data will be lost)" -ForegroundColor Yellow

    $confirm = Read-Host "`nType 'yes' to confirm cleanup"

    if ($confirm -eq "yes") {
        Write-Step "Removing containers and volumes..."
        docker compose down -v

        Write-Step "Removing images..."
        $images = docker images --format "{{.Repository}}:{{.Tag}} {{.ID}}" | Select-String "nexus"
        foreach ($image in $images) {
            $imageId = ($image -split " ")[1]
            docker rmi $imageId -f
        }

        Write-Success "Cleanup complete!"
        Write-Info "Run option 1 to rebuild and start fresh"
    } else {
        Write-Info "Cleanup cancelled"
    }
}

# Main loop
do {
    Show-Menu
    $choice = Read-Host "Enter choice (1-9)"

    switch ($choice) {
        "1" { Start-Services }
        "2" { Restart-Services }
        "3" { Start-Fresh }
        "4" { Stop-Services }
        "5" { Show-Status }
        "6" { Show-Logs }
        "7" { Run-Diagnostic }
        "8" { Clean-Up }
        "9" {
            Write-Host "`nGoodbye! 👋" -ForegroundColor Green
            exit 0
        }
        default {
            Write-Fail "Invalid choice. Please enter 1-9"
        }
    }

    if ($choice -ne "9") {
        Write-Host "`nPress Enter to return to menu..." -ForegroundColor Gray
        Read-Host
    }

} while ($true)

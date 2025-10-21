# Nexus Analyzer Diagnostic Script
# Checks Docker Desktop connectivity and project setup
# Run this from your project directory: C:\Users\markw\nexus-analyzer-new\nexus-analyzer-new

Write-Host @"
╔══════════════════════════════════════════╗
║   Nexus Analyzer Docker Diagnostic       ║
║   Troubleshooting Tool                   ║
╚══════════════════════════════════════════╝
"@ -ForegroundColor Cyan

# Get current directory
$currentDir = Get-Location
Write-Host "`nCurrent Directory: $currentDir" -ForegroundColor Gray

Write-Host "`n1. Project Files Check:" -ForegroundColor Yellow
$requiredFiles = @(
    "docker-compose.yml",
    ".env.example",
    "backend/Dockerfile",
    "frontend/Dockerfile",
    "backend/requirements.txt",
    "frontend/package.json"
)

foreach ($file in $requiredFiles) {
    $exists = Test-Path $file
    $icon = if ($exists) { "✓" } else { "✗" }
    $color = if ($exists) { "Green" } else { "Red" }
    Write-Host "   $icon $file" -ForegroundColor $color
}

$envExists = Test-Path ".env"
if ($envExists) {
    Write-Host "   ✓ .env file exists" -ForegroundColor Green
} else {
    Write-Host "   ✗ .env file NOT found (will need to create from .env.example)" -ForegroundColor Yellow
}

Write-Host "`n2. Docker Desktop Status:" -ForegroundColor Yellow
try {
    $dockerVersion = docker --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✓ Docker installed: $dockerVersion" -ForegroundColor Green
    } else {
        throw "Docker command failed"
    }
} catch {
    Write-Host "   ✗ Docker not found or not in PATH" -ForegroundColor Red
    Write-Host "   → Install Docker Desktop from: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    Write-Host "   Stopping diagnostic..." -ForegroundColor Red
    exit 1
}

Write-Host "`n3. Docker Daemon Connectivity:" -ForegroundColor Yellow
try {
    docker ps 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✓ Docker daemon is running and accessible" -ForegroundColor Green
    } else {
        throw "Cannot connect"
    }
} catch {
    Write-Host "   ✗ Cannot connect to Docker daemon" -ForegroundColor Red
    Write-Host "   → Start Docker Desktop and wait 60 seconds for it to initialize" -ForegroundColor Yellow
    Write-Host "   → Check system tray for Docker whale icon 🐋" -ForegroundColor Yellow
    Write-Host "   Stopping diagnostic..." -ForegroundColor Red
    exit 1
}

Write-Host "`n4. Docker Compose Version:" -ForegroundColor Yellow
try {
    $composeVersion = docker compose version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✓ Docker Compose: $composeVersion" -ForegroundColor Green
    } else {
        Write-Host "   ✗ Docker Compose not available" -ForegroundColor Red
    }
} catch {
    Write-Host "   ✗ Docker Compose command failed" -ForegroundColor Red
}

Write-Host "`n5. Port Availability Check:" -ForegroundColor Yellow
$ports = @(
    @{Port=5432; Service="PostgreSQL"},
    @{Port=6379; Service="Redis"},
    @{Port=8000; Service="Backend API"},
    @{Port=9000; Service="MinIO"},
    @{Port=9001; Service="MinIO Console"},
    @{Port=3000; Service="Frontend"}
)

$portConflicts = @()
foreach ($portInfo in $ports) {
    $port = $portInfo.Port
    $service = $portInfo.Service

    try {
        $connection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
        if ($connection) {
            $process = Get-Process -Id $connection.OwningProcess -ErrorAction SilentlyContinue
            Write-Host "   ✗ Port $port ($service): IN USE by $($process.ProcessName) (PID: $($connection.OwningProcess))" -ForegroundColor Red
            $portConflicts += $port
        } else {
            Write-Host "   ✓ Port $port ($service): Available" -ForegroundColor Green
        }
    } catch {
        Write-Host "   ✓ Port $port ($service): Available" -ForegroundColor Green
    }
}

if ($portConflicts.Count -gt 0) {
    Write-Host "`n   ⚠ WARNING: Ports in use. You may need to:" -ForegroundColor Yellow
    Write-Host "   → Stop conflicting applications" -ForegroundColor Yellow
    Write-Host "   → Change ports in .env file" -ForegroundColor Yellow
    Write-Host "   → Use 'docker compose down' if old containers are running" -ForegroundColor Yellow
}

Write-Host "`n6. Docker Containers Status:" -ForegroundColor Yellow
try {
    $containers = docker compose ps --format json 2>&1
    if ($LASTEXITCODE -eq 0 -and $containers) {
        Write-Host "   Nexus Analyzer containers:" -ForegroundColor Gray
        docker compose ps
    } else {
        Write-Host "   No containers currently running" -ForegroundColor Gray
    }
} catch {
    Write-Host "   No containers currently running" -ForegroundColor Gray
}

Write-Host "`n7. Docker Images:" -ForegroundColor Yellow
$images = docker images --format "{{.Repository}}:{{.Tag}}" | Select-String -Pattern "nexus"
if ($images) {
    foreach ($image in $images) {
        Write-Host "   $image" -ForegroundColor Gray
    }
} else {
    Write-Host "   No Nexus Analyzer images built yet (normal for first run)" -ForegroundColor Gray
}

Write-Host "`n8. Docker Volumes:" -ForegroundColor Yellow
$volumes = docker volume ls --format "{{.Name}}" | Select-String -Pattern "nexus"
if ($volumes) {
    foreach ($volume in $volumes) {
        Write-Host "   $volume" -ForegroundColor Gray
    }
} else {
    Write-Host "   No volumes created yet" -ForegroundColor Gray
}

Write-Host "`n9. Environment Configuration:" -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "   ✓ .env file exists" -ForegroundColor Green
    Write-Host "`n   Key variables (sensitive values hidden):" -ForegroundColor Gray

    $envContent = Get-Content .env | Where-Object { $_ -match "^[A-Z]" -and $_ -notmatch "^#" }
    $displayCount = 0
    foreach ($line in $envContent) {
        if ($displayCount -ge 15) {
            Write-Host "      ... (and more)" -ForegroundColor DarkGray
            break
        }
        if ($line -match "(PASSWORD|SECRET|KEY)=") {
            $varName = $line.Split('=')[0]
            Write-Host "      $varName=***" -ForegroundColor DarkGray
        } else {
            Write-Host "      $line" -ForegroundColor DarkGray
        }
        $displayCount++
    }

    # Check for required SECRET_KEY
    $secretKey = $envContent | Select-String "^SECRET_KEY="
    if ($secretKey -and $secretKey -match "your-secret-key|change-in-production") {
        Write-Host "`n   ⚠ WARNING: SECRET_KEY appears to be using default value!" -ForegroundColor Red
        Write-Host "   → Generate new key: openssl rand -hex 32" -ForegroundColor Yellow
        Write-Host "   → Or use PowerShell: -join ((1..32) | ForEach-Object { '{0:x2}' -f (Get-Random -Maximum 256) })" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ✗ .env file NOT found" -ForegroundColor Red
    if (Test-Path ".env.example") {
        Write-Host "   → Creating .env from .env.example..." -ForegroundColor Yellow
        Copy-Item .env.example .env
        Write-Host "   ✓ .env file created!" -ForegroundColor Green
        Write-Host "   → IMPORTANT: Edit .env and set your SECRET_KEY" -ForegroundColor Yellow
    }
}

Write-Host "`n10. System Resources:" -ForegroundColor Yellow
try {
    $mem = Get-CimInstance Win32_OperatingSystem
    $totalRAM = [math]::Round($mem.TotalVisibleMemorySize/1MB, 2)
    $freeRAM = [math]::Round($mem.FreePhysicalMemory/1MB, 2)
    $usedRAM = $totalRAM - $freeRAM

    Write-Host "   Total RAM: $totalRAM GB" -ForegroundColor Gray
    Write-Host "   Used RAM:  $usedRAM GB" -ForegroundColor Gray
    Write-Host "   Free RAM:  $freeRAM GB" -ForegroundColor Gray

    if ($freeRAM -lt 2) {
        Write-Host "   ⚠ Low memory available. Docker may perform slowly." -ForegroundColor Yellow
    }
} catch {
    Write-Host "   Could not retrieve system info" -ForegroundColor Gray
}

Write-Host "`n11. Recent Docker Logs (if containers running):" -ForegroundColor Yellow
try {
    $logs = docker compose logs --tail=5 2>&1
    if ($LASTEXITCODE -eq 0 -and $logs -and $logs.Count -gt 0) {
        $logs | Select-Object -First 10 | ForEach-Object {
            Write-Host "   $_" -ForegroundColor DarkGray
        }
    } else {
        Write-Host "   No logs available (containers not running)" -ForegroundColor Gray
    }
} catch {
    Write-Host "   No logs available" -ForegroundColor Gray
}

Write-Host "`n═══════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "Diagnostic Complete!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════" -ForegroundColor Cyan

# Summary and recommendations
Write-Host "`n📋 SUMMARY & NEXT STEPS:" -ForegroundColor Yellow

$canStart = $true

if (-not (Test-Path "docker-compose.yml")) {
    Write-Host "   ✗ Missing docker-compose.yml - cannot start" -ForegroundColor Red
    $canStart = $false
}

if (-not (Test-Path ".env")) {
    Write-Host "   ⚠ Missing .env file - create from .env.example" -ForegroundColor Yellow
    Write-Host "     Command: copy .env.example .env" -ForegroundColor Cyan
    $canStart = $false
}

if ($portConflicts.Count -gt 0) {
    Write-Host "   ⚠ Port conflicts detected - resolve before starting" -ForegroundColor Yellow
}

if ($canStart) {
    Write-Host "`n✅ System ready to start!" -ForegroundColor Green
    Write-Host "`nTo start the application:" -ForegroundColor White
    Write-Host "   docker compose up -d" -ForegroundColor Cyan
    Write-Host "`nOr use the quick-start script:" -ForegroundColor White
    Write-Host "   .\quick-start.ps1" -ForegroundColor Cyan
} else {
    Write-Host "`n⚠ Please resolve issues above before starting" -ForegroundColor Yellow
}

Write-Host "`nUseful Commands:" -ForegroundColor White
Write-Host "   View status:    docker compose ps" -ForegroundColor Cyan
Write-Host "   View logs:      docker compose logs -f" -ForegroundColor Cyan
Write-Host "   Stop all:       docker compose down" -ForegroundColor Cyan
Write-Host "   Fresh start:    docker compose down -v && docker compose up -d" -ForegroundColor Cyan
Write-Host ""

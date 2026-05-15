# =============================================================
# Plataforma DTI Níjar — Setup inicial Windows
# =============================================================
# Comprueba prerequisitos, crea .env y valida puertos.
# Ejecutar UNA VEZ tras descomprimir el proyecto.
# =============================================================

$ErrorActionPreference = "Stop"

# Localizar la raíz del proyecto (carpeta padre del script)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Plataforma DTI Níjar — Setup inicial" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Carpeta del proyecto: $ProjectRoot"
Write-Host ""

# -------------------------------------------------------------
# 1. Comprobar Docker Desktop
# -------------------------------------------------------------
Write-Host "[1/6] Comprobando Docker Desktop..." -ForegroundColor Yellow

try {
    $dockerVersion = docker version --format '{{.Server.Version}}' 2>$null
    if (-not $dockerVersion) { throw "Docker no responde" }
    Write-Host "      OK — Docker Engine $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "      ERROR — Docker Desktop no esta arrancado o no esta instalado." -ForegroundColor Red
    Write-Host ""
    Write-Host "      Soluciones:"
    Write-Host "      1) Instalar Docker Desktop desde https://www.docker.com/products/docker-desktop"
    Write-Host "      2) Asegurarse de que esta arrancado (icono ballena en bandeja)"
    Write-Host "      3) Esperar a que el icono este en verde (puede tardar ~30s al iniciar)"
    Write-Host ""
    exit 1
}

# Comprobar docker compose v2
try {
    $composeVersion = docker compose version --short 2>$null
    if (-not $composeVersion) { throw "docker compose v2 no disponible" }
    Write-Host "      OK — Docker Compose $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "      ERROR — Docker Compose v2 no detectado." -ForegroundColor Red
    Write-Host "      Actualiza Docker Desktop a una version reciente (>= 4.x)."
    exit 1
}

# -------------------------------------------------------------
# 2. Comprobar WSL2
# -------------------------------------------------------------
Write-Host ""
Write-Host "[2/6] Comprobando backend WSL2..." -ForegroundColor Yellow
try {
    $wslStatus = wsl --status 2>$null | Out-String
    if ($wslStatus -match "WSL 2|version: 2") {
        Write-Host "      OK — WSL2 disponible" -ForegroundColor Green
    } else {
        Write-Host "      AVISO — No se detecta WSL2 como version por defecto." -ForegroundColor Yellow
        Write-Host "      Docker Desktop debe usar WSL2 backend para mejor rendimiento."
        Write-Host "      Habilitar en: Docker Desktop -> Settings -> General -> Use WSL 2 based engine"
    }
} catch {
    Write-Host "      AVISO — wsl no responde. Si Docker Desktop usa Hyper-V, ignora este aviso." -ForegroundColor Yellow
}

# -------------------------------------------------------------
# 3. Comprobar puertos disponibles
# -------------------------------------------------------------
Write-Host ""
Write-Host "[3/6] Comprobando puertos..." -ForegroundColor Yellow

$ports = @{
    8000 = "API (Swagger / dashboards)"
    5432 = "PostgreSQL"
    6379 = "Redis"
    1883 = "MQTT broker"
    9001 = "MQTT WebSocket"
    5005 = "Rasa server"
}

$portConflicts = @()
foreach ($port in $ports.Keys) {
    $inUse = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($inUse) {
        $proc = $null
        try { $proc = Get-Process -Id $inUse[0].OwningProcess -ErrorAction SilentlyContinue } catch {}
        $procName = if ($proc) { $proc.ProcessName } else { "desconocido" }
        Write-Host "      AVISO — Puerto $port ocupado por $procName ($($ports[$port]))" -ForegroundColor Yellow
        $portConflicts += $port
    } else {
        Write-Host "      OK — Puerto $port libre" -ForegroundColor Green
    }
}

if ($portConflicts.Count -gt 0) {
    Write-Host ""
    Write-Host "      Hay puertos ocupados. Opciones:"
    Write-Host "      1) Detener los servicios que los ocupan (ej. Postgres local en 5432)"
    Write-Host "      2) Editar docker-compose.yml y cambiar los puertos publicados"
    Write-Host "      3) Continuar de todas formas (start.ps1 fallara si el puerto esta ocupado)"
}

# -------------------------------------------------------------
# 4. Crear .env si no existe
# -------------------------------------------------------------
Write-Host ""
Write-Host "[4/6] Configurando archivo .env..." -ForegroundColor Yellow

$envPath = Join-Path $ProjectRoot ".env"
$envExamplePath = Join-Path $ProjectRoot ".env.example"

if (Test-Path $envPath) {
    Write-Host "      AVISO — Ya existe .env, no se sobrescribe" -ForegroundColor Yellow
} else {
    if (-not (Test-Path $envExamplePath)) {
        Write-Host "      ERROR — No se encuentra .env.example en la raiz del proyecto." -ForegroundColor Red
        Write-Host "      Asegurate de haber descomprimido el proyecto correctamente."
        exit 1
    }

    Copy-Item $envExamplePath $envPath
    Write-Host "      OK — .env creado desde .env.example" -ForegroundColor Green

    # Generar SECRET_KEY automaticamente
    $secret = -join ((1..43) | ForEach-Object { [char[]]"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" | Get-Random })
    (Get-Content $envPath) -replace '^SECRET_KEY=.*$', "SECRET_KEY=$secret" | Set-Content $envPath -Encoding UTF8
    Write-Host "      OK — SECRET_KEY generado aleatoriamente" -ForegroundColor Green
}

# -------------------------------------------------------------
# 5. Comprobar recursos disponibles
# -------------------------------------------------------------
Write-Host ""
Write-Host "[5/6] Comprobando recursos del sistema..." -ForegroundColor Yellow

$totalRAM_GB = [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 1)
$freeRAM_GB = [math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB / 1024, 1)

Write-Host "      RAM total: $totalRAM_GB GB"
Write-Host "      RAM libre actual: $freeRAM_GB GB"

if ($totalRAM_GB -lt 8) {
    Write-Host "      AVISO — Menos de 8 GB de RAM total. Solo se recomienda perfil 'min'." -ForegroundColor Yellow
} elseif ($totalRAM_GB -lt 16) {
    Write-Host "      AVISO — Con 8-16 GB de RAM evita arrancar Rasa." -ForegroundColor Yellow
    Write-Host "             Usa perfil 'workers' (sin Rasa) en lugar de 'full'."
} else {
    Write-Host "      OK — RAM suficiente para perfil 'full' (con Rasa)" -ForegroundColor Green
}

# -------------------------------------------------------------
# 6. Pre-pull de imagenes (opcional)
# -------------------------------------------------------------
Write-Host ""
Write-Host "[6/6] Pre-descarga de imagenes Docker (puede tardar varios minutos)..." -ForegroundColor Yellow
Write-Host "      Saltando si quieres iniciar mas rapido (Ctrl+C en 5s)."
Start-Sleep -Seconds 5

try {
    docker compose pull db redis mqtt 2>&1 | Where-Object { $_ -match "Pull|Pulling|Downloaded|complete" } | ForEach-Object {
        Write-Host "      $_"
    }
    Write-Host "      OK — Imagenes base descargadas" -ForegroundColor Green
} catch {
    Write-Host "      AVISO — No se pudieron pre-descargar las imagenes." -ForegroundColor Yellow
    Write-Host "      Se descargaran al ejecutar start.ps1 por primera vez."
}

# -------------------------------------------------------------
# Listo
# -------------------------------------------------------------
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host " Setup completado correctamente" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host " Siguiente paso: arrancar la plataforma" -ForegroundColor Cyan
Write-Host ""
Write-Host "   .\windows\start.ps1                    (solo API + dependencias minimas)"
Write-Host "   .\windows\start.ps1 -Workers           (con workers MQTT y Social Listening)"
Write-Host "   .\windows\start.ps1 -Workers -Rasa     (todo: workers + Rasa)"
Write-Host ""
Write-Host " O por doble clic en:"
Write-Host "   windows\start.bat"
Write-Host ""

# =============================================================
# Plataforma DTI Níjar — Arranque local Windows
# =============================================================
# Uso:
#   .\windows\start.ps1                    Solo API + DB + Redis + MQTT (perfil minimo)
#   .\windows\start.ps1 -Workers           Anade MQTT subscriber + Social worker
#   .\windows\start.ps1 -Workers -Rasa     Todo: workers + Rasa entrenado
#   .\windows\start.ps1 -NoBrowser         No abrir navegador automaticamente
# =============================================================

[CmdletBinding()]
param(
    [switch]$Workers,
    [switch]$Rasa,
    [switch]$NoBrowser,
    [switch]$Detached = $true
)

$ErrorActionPreference = "Stop"

# Localizar la raíz del proyecto
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Plataforma DTI Níjar — Arranque local" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Comprobar Docker arrancado
Write-Host "[1/6] Comprobando Docker Desktop..." -ForegroundColor Yellow
try {
    docker version --format '{{.Server.Version}}' 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { throw }
    Write-Host "      OK" -ForegroundColor Green
} catch {
    Write-Host "      ERROR — Docker Desktop no esta arrancado." -ForegroundColor Red
    Write-Host "      Inicia Docker Desktop y espera a que el icono se ponga verde."
    exit 1
}

# Comprobar .env
if (-not (Test-Path ".env")) {
    Write-Host "      AVISO — No existe .env, ejecuta primero windows\setup.ps1" -ForegroundColor Yellow
    Write-Host "      Creandolo automaticamente desde .env.example..."
    if (-not (Test-Path ".env.example")) {
        Write-Host "      ERROR — No existe .env.example tampoco. Estructura del proyecto incorrecta." -ForegroundColor Red
        exit 1
    }
    Copy-Item ".env.example" ".env"
    Write-Host "      OK — .env creado" -ForegroundColor Green
}

# Construir lista de perfiles
$ProfileArgs = @()
if ($Workers) { $ProfileArgs += @("--profile", "workers") }
if ($Rasa)    { $ProfileArgs += @("--profile", "rasa") }

$perfilDesc = "minimo (api + db + redis + mqtt)"
if ($Workers -and $Rasa) { $perfilDesc = "completo (api + workers + rasa)" }
elseif ($Workers)         { $perfilDesc = "con workers (api + workers)" }

Write-Host ""
Write-Host "[2/6] Perfil de arranque: $perfilDesc" -ForegroundColor Yellow

# -------------------------------------------------------------
# Levantar servicios base
# -------------------------------------------------------------
Write-Host ""
Write-Host "[3/6] Levantando servicios base (PostgreSQL, Redis, MQTT)..." -ForegroundColor Yellow
& docker compose up -d db redis mqtt
if ($LASTEXITCODE -ne 0) {
    Write-Host "      ERROR — Fallo al levantar servicios base." -ForegroundColor Red
    Write-Host "      Posibles causas: puertos ocupados, Docker sin recursos."
    Write-Host "      Comprueba con: .\windows\status.ps1"
    exit 1
}

# -------------------------------------------------------------
# Esperar a PostgreSQL
# -------------------------------------------------------------
Write-Host ""
Write-Host "[4/6] Esperando a PostgreSQL..." -ForegroundColor Yellow
$maxAttempts = 30
$ok = $false
for ($i = 1; $i -le $maxAttempts; $i++) {
    docker compose exec -T db pg_isready -U nijar -d nijar_dti 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "      OK — PostgreSQL responde (en $i intentos)" -ForegroundColor Green
        $ok = $true
        break
    }
    Start-Sleep -Seconds 1
    Write-Host "      ... intento $i/$maxAttempts" -NoNewline
    Write-Host "`r" -NoNewline
}
if (-not $ok) {
    Write-Host ""
    Write-Host "      ERROR — PostgreSQL no responde tras $maxAttempts intentos." -ForegroundColor Red
    Write-Host "      Logs: docker compose logs db"
    exit 1
}

# -------------------------------------------------------------
# Migraciones Alembic + datos seed
# -------------------------------------------------------------
Write-Host ""
Write-Host "[5/6] Aplicando migraciones y cargando datos seed (puede tardar 1-2 min en primer arranque)..." -ForegroundColor Yellow

& docker compose run --rm api alembic upgrade head
if ($LASTEXITCODE -ne 0) {
    Write-Host "      ERROR — Fallo al aplicar migraciones." -ForegroundColor Red
    exit 1
}
Write-Host "      OK — Migraciones aplicadas" -ForegroundColor Green

& docker compose run --rm api python -m nijar_dti.data.seed_loader
if ($LASTEXITCODE -ne 0) {
    Write-Host "      AVISO — Carga de datos seed devolvio error (quiza ya cargados)." -ForegroundColor Yellow
} else {
    Write-Host "      OK — Datos seed cargados" -ForegroundColor Green
}

# -------------------------------------------------------------
# Levantar API + perfiles
# -------------------------------------------------------------
Write-Host ""
Write-Host "[6/6] Levantando API y servicios del perfil seleccionado..." -ForegroundColor Yellow

if ($Rasa) {
    Write-Host "      Pre-entrenando Rasa (esto puede tardar 3-5 min en primer arranque)..." -ForegroundColor Yellow
    & docker compose --profile rasa-train run --rm rasa-trainer
    if ($LASTEXITCODE -ne 0) {
        Write-Host "      AVISO — Entrenamiento de Rasa fallo. Continuando sin Rasa." -ForegroundColor Yellow
    }
}

$composeArgs = @("compose") + $ProfileArgs + @("up", "-d", "api")
if ($Workers) { $composeArgs += @("mqtt-subscriber", "social-worker") }
if ($Rasa)    { $composeArgs += "rasa" }

& docker @composeArgs
if ($LASTEXITCODE -ne 0) {
    Write-Host "      ERROR — Fallo al arrancar la API." -ForegroundColor Red
    Write-Host "      Logs: docker compose logs api"
    exit 1
}

# -------------------------------------------------------------
# Health check
# -------------------------------------------------------------
Write-Host ""
Write-Host "Esperando a que la API responda..." -ForegroundColor Yellow

$apiReady = $false
for ($i = 1; $i -le 30; $i++) {
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        if ($r.StatusCode -eq 200) {
            $apiReady = $true
            break
        }
    } catch {
        Start-Sleep -Seconds 2
    }
}

if (-not $apiReady) {
    Write-Host "      AVISO — La API no responde tras 60s. Revisa logs: docker compose logs -f api" -ForegroundColor Yellow
} else {
    Write-Host "      OK — API operativa" -ForegroundColor Green
}

# -------------------------------------------------------------
# Resumen final
# -------------------------------------------------------------
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host " Plataforma operativa" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host " Endpoints disponibles:" -ForegroundColor Cyan
Write-Host "   Swagger UI:  http://localhost:8000/docs"
Write-Host "   ReDoc:       http://localhost:8000/redoc"
Write-Host "   Dashboard:   http://localhost:8000/dashboard"
Write-Host "   Tótem:       http://localhost:8000/totem"
Write-Host "   Health:      http://localhost:8000/api/v1/health"
if ($Rasa) {
    Write-Host "   Rasa:        http://localhost:5005"
}
Write-Host ""
Write-Host " Credenciales por defecto del admin:" -ForegroundColor Cyan
Write-Host "   email: admin@nijar.es"
Write-Host "   pass:  CambiarEnPrimerArranque#2026"
Write-Host ""
Write-Host " Comandos utiles:" -ForegroundColor Cyan
Write-Host "   .\windows\status.ps1     Ver estado de los servicios"
Write-Host "   .\windows\logs.ps1       Ver logs en tiempo real"
Write-Host "   .\windows\stop.ps1       Parar todo"
Write-Host "   .\windows\reset.ps1      Parar y borrar volumenes (empezar de cero)"
Write-Host ""

# Abrir navegador
if ((-not $NoBrowser) -and $apiReady) {
    Write-Host "Abriendo navegador en Swagger UI..." -ForegroundColor Yellow
    Start-Process "http://localhost:8000/docs"
}

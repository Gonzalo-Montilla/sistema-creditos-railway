param(
    [int]$Port = 8000,
    [switch]$SkipInstall,
    [switch]$NoMigrate,
    [switch]$CheckOnly
)

$ErrorActionPreference = "Stop"

function Write-Step($msg) {
    Write-Host ""
    Write-Host "==> $msg" -ForegroundColor Cyan
}

function Get-PythonLauncher {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return "py"
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return "python"
    }
    throw "No se encontro Python. Instala Python 3.12+ y vuelve a intentar."
}

if (-not (Test-Path ".\manage.py")) {
    throw "No se encontro manage.py. Ejecuta este script desde la raiz del proyecto."
}

$venvPath = ".\.venv"
$activatePath = Join-Path $venvPath "Scripts\Activate.ps1"
$pythonLauncher = Get-PythonLauncher

Write-Step "Preparando entorno virtual"
if (-not (Test-Path $activatePath)) {
    & $pythonLauncher -m venv .venv
}

. $activatePath

Write-Step "Python activo"
python --version

if (-not $SkipInstall) {
    Write-Step "Actualizando herramientas base de pip"
    python -m pip install --upgrade pip setuptools wheel

    Write-Step "Instalando dependencias del proyecto"
    pip install -r requirements.txt
} else {
    Write-Step "Se omite instalacion de dependencias (SkipInstall)"
}

if (-not $NoMigrate) {
    Write-Step "Aplicando migraciones"
    python manage.py migrate
} else {
    Write-Step "Se omiten migraciones (NoMigrate)"
}

if ($CheckOnly) {
    Write-Step "Chequeo completo OK (CheckOnly). No se inicia servidor."
    exit 0
}

Write-Step "Levantando servidor local en http://127.0.0.1:$Port/"
python manage.py runserver "127.0.0.1:$Port"

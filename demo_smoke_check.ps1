param(
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

function Step($msg) {
    Write-Host ""
    Write-Host "==> $msg" -ForegroundColor Cyan
}

function Fail($msg) {
    Write-Host ""
    Write-Host "ERROR: $msg" -ForegroundColor Red
    exit 1
}

function Get-HttpStatusCode($url) {
    $code = & curl.exe -s -o NUL -w "%{http_code}" -L $url
    if (-not $code) {
        throw "No se pudo obtener codigo HTTP para $url"
    }
    return [int]$code
}

if (-not (Test-Path ".\manage.py")) {
    Fail "Ejecuta este script en la raiz del proyecto (donde esta manage.py)."
}

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    Fail "No existe .venv. Ejecuta primero .\start_local.ps1 para prepararlo."
}

Step "Chequeo Django"
& .\.venv\Scripts\python.exe manage.py check
if ($LASTEXITCODE -ne 0) { Fail "Django check fallo." }

Step "Chequeo de migraciones pendientes"
& .\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
if ($LASTEXITCODE -ne 0) { Fail "Hay cambios de modelos sin migracion." }

Step "Levantando servidor temporal para smoke test"
$stdout = Join-Path $env:TEMP "demo_smoke_out.log"
$stderr = Join-Path $env:TEMP "demo_smoke_err.log"
if (Test-Path $stdout) { Remove-Item $stdout -Force }
if (Test-Path $stderr) { Remove-Item $stderr -Force }

$proc = Start-Process -FilePath ".\.venv\Scripts\python.exe" `
    -ArgumentList @("manage.py", "runserver", "127.0.0.1:$Port", "--noreload") `
    -RedirectStandardOutput $stdout `
    -RedirectStandardError $stderr `
    -PassThru

try {
    $base = "http://127.0.0.1:$Port"
    $ready = $false
    for ($i = 0; $i -lt 20; $i++) {
        Start-Sleep -Milliseconds 700
        try {
            $r = Invoke-WebRequest -Uri "$base/login/" -UseBasicParsing -TimeoutSec 3
            if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 500) {
                $ready = $true
                break
            }
        } catch {
            # sigue intentando
        }
    }

    if (-not $ready) {
        $errOut = ""
        if (Test-Path $stderr) { $errOut = (Get-Content $stderr -Raw) }
        Fail "El servidor no respondio a tiempo. Error: $errOut"
    }

    Step "Validando rutas clave"
    $targets = @(
        @{ Url = "$base/login/"; Name = "Login"; Allowed = @(200) },
        @{ Url = "$base/dashboard/"; Name = "Dashboard"; Allowed = @(200, 302) },
        @{ Url = "$base/creditos/"; Name = "Creditos"; Allowed = @(200, 302) },
        @{ Url = "$base/cierre-cobro-diario/"; Name = "Cierre diario"; Allowed = @(200, 302) }
    )

    foreach ($t in $targets) {
        $code = Get-HttpStatusCode $t.Url

        if ($t.Allowed -notcontains $code) {
            Fail "$($t.Name) devolvio HTTP $code (esperado: $($t.Allowed -join ', '))."
        }

        Write-Host "OK  $($t.Name): HTTP $code" -ForegroundColor Green
    }

    Step "Smoke test completado OK"
    Write-Host "Sistema listo para demo tecnica basica." -ForegroundColor Green
}
finally {
    if ($proc -and -not $proc.HasExited) {
        Stop-Process -Id $proc.Id -Force
    }
}

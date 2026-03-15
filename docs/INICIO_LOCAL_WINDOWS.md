# Inicio local en Windows (PowerShell)

Guia rapida para levantar el sistema sin errores de entorno.

## Opcion recomendada (1 comando)

Desde la raiz del proyecto:

```powershell
.\start_local.ps1
```

Alternativa para doble clic o CMD:

```bat
start_local.bat
```

Parametros utiles:

```powershell
.\start_local.ps1 -Port 8080
.\start_local.ps1 -SkipInstall
.\start_local.ps1 -NoMigrate
.\start_local.ps1 -CheckOnly
```

## 1) Crear y activar entorno virtual

```powershell
cd "C:\Proyectos\sistema-creditos"
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea scripts:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 2) Instalar dependencias

```powershell
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

## 3) Migraciones y servidor

```powershell
python manage.py migrate
python manage.py runserver
```

Abrir en navegador:

- http://127.0.0.1:8000/

## 4) Si vuelve a fallar por entorno

Recrear el entorno (limpio):

```powershell
deactivate
Remove-Item -Recurse -Force ".\.venv"
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Nota importante

El proyecto usa SQLite en local por defecto (si no existe `DATABASE_URL`), por eso deberia iniciar sin configuraciones extra de PostgreSQL.

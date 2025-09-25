@echo off
rem Script para verificar que las automatizaciones funcionan correctamente
rem Ejecutar manualmente cuando quieras verificar

cd /d "C:\Users\USUARIO\Documents\Sistema-Creditos"

echo.
echo ==========================================
echo VERIFICACION DE AUTOMATIZACIONES
echo ==========================================
echo.

echo 🔍 Verificando sistema...
python manage.py ejecutar_tareas_automaticas --fecha=%date:~-4%-%date:~3,2%-%date:~0,2%

echo.
echo 📋 Estado de la base de datos:
python diagnosticar_tareas.py

echo.
echo 📊 Logs recientes:
if exist logs\automatizaciones.log (
    echo === ULTIMOS LOGS ===
    type logs\automatizaciones.log | find /v "" | more
) else (
    echo No hay logs de automatizaciones aún
)

echo.
echo ==========================================
echo VERIFICACION COMPLETADA
echo ==========================================
pause
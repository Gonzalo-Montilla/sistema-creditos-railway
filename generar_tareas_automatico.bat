@echo off
rem Script para automatización completa de tareas diarias
rem Ejecutar desde Windows Task Scheduler cada día a las 6:00 AM

cd /d "C:\Users\USUARIO\Documents\Sistema-Creditos"

rem Crear directorio de logs si no existe
if not exist logs mkdir logs

echo [%date% %time%] === INICIANDO AUTOMATIZACIONES DIARIAS === >> logs\automatizaciones.log
echo [%date% %time%] Iniciando automatizaciones...

rem Ejecutar todas las automatizaciones
python manage.py ejecutar_tareas_automaticas >> logs\automatizaciones.log 2>&1

echo [%date% %time%] Automatizaciones completadas.
echo [%date% %time%] === FIN AUTOMATIZACIONES DIARIAS === >> logs\automatizaciones.log
echo. >> logs\automatizaciones.log

rem Mantener solo los últimos 30 días de logs (opcional)
forfiles /p logs /s /m *.log /d -30 /c "cmd /c del @path" 2>nul

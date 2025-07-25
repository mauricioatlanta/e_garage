@echo off
REM setup_backup_windows.bat - Configurar Backup Automático en Windows
echo =========================================
echo    E-GARAGE BACKUP AUTOMATICO WINDOWS
echo =========================================

REM Crear directorio para logs si no existe
if not exist "logs" mkdir logs
if not exist "backups" mkdir backups

echo.
echo Configurando backup automatico en Windows...

REM Crear archivo batch para ejecutar backup
echo @echo off > run_backup.bat
echo cd /d "%~dp0" >> run_backup.bat
echo python backup_scheduler.py >> run_backup.bat

REM Crear archivo batch para monitoreo
echo @echo off > run_monitoring.bat
echo cd /d "%~dp0" >> run_monitoring.bat
echo python monitoring_setup.py >> run_monitoring.bat

echo.
echo Archivos creados:
echo - run_backup.bat (ejecutar backup manual)
echo - run_monitoring.bat (ejecutar monitoreo manual)

echo.
echo =========================================
echo INSTRUCCIONES PARA PROGRAMAR TAREAS:
echo =========================================
echo.
echo 1. Abrir "Programador de tareas" (taskschd.msc)
echo 2. Crear tarea basica...
echo 3. Nombre: "E-Garage Backup Diario"
echo 4. Desencadenador: Diariamente a las 02:00
echo 5. Accion: Iniciar programa
echo 6. Programa: %CD%\run_backup.bat
echo 7. Directorio inicial: %CD%
echo.
echo TAREA DE MONITOREO:
echo 1. Nombre: "E-Garage Monitoreo"
echo 2. Desencadenador: Repetir cada 15 minutos
echo 3. Programa: %CD%\run_monitoring.bat
echo.
echo =========================================

REM Intentar crear las tareas automaticamente (requiere permisos admin)
echo.
echo Intentando crear tareas automaticamente...
echo (Requiere permisos de administrador)

REM Backup diario
schtasks /create /tn "E-Garage Backup Diario" /tr "%CD%\run_backup.bat" /sc daily /st 02:00 /f 2>nul
if %errorlevel% equ 0 (
    echo ✓ Tarea de backup creada exitosamente
) else (
    echo ✗ No se pudo crear la tarea de backup automaticamente
    echo   Crearla manualmente siguiendo las instrucciones arriba
)

REM Monitoreo cada 15 minutos
schtasks /create /tn "E-Garage Monitoreo" /tr "%CD%\run_monitoring.bat" /sc minute /mo 15 /f 2>nul
if %errorlevel% equ 0 (
    echo ✓ Tarea de monitoreo creada exitosamente
) else (
    echo ✗ No se pudo crear la tarea de monitoreo automaticamente
    echo   Crearla manualmente siguiendo las instrucciones arriba
)

echo.
echo =========================================
echo VERIFICAR TAREAS CREADAS:
echo =========================================
echo.
echo Listando tareas de E-Garage:
schtasks /query /tn "E-Garage*" 2>nul
if %errorlevel% neq 0 (
    echo No se encontraron tareas de E-Garage
)

echo.
echo =========================================
echo COMANDOS UTILES:
echo =========================================
echo.
echo Ejecutar backup manual:
echo   run_backup.bat
echo.
echo Ejecutar monitoreo manual:
echo   run_monitoring.bat
echo.
echo Ver logs:
echo   type logs\backup_scheduler.log
echo   type logs\monitoring.log
echo.
echo Eliminar tareas:
echo   schtasks /delete /tn "E-Garage Backup Diario" /f
echo   schtasks /delete /tn "E-Garage Monitoreo" /f
echo.

pause

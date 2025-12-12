@echo off
echo ========================================
echo   PROBAR PWA EN CELULAR - eGarage
echo ========================================
echo.

:: Obtener IP local automáticamente
echo [1/4] Obteniendo tu IP local...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set IP=%%a
    goto :ip_found
)
:ip_found
set IP=%IP:~1%

if "%IP%"=="" (
    echo ERROR: No se pudo detectar la IP automaticamente
    echo.
    echo Por favor, ejecuta 'ipconfig' y busca tu "Direccion IPv4"
    echo Luego inicia el servidor manualmente con:
    echo    python manage.py runserver 0.0.0.0:8000
    pause
    exit /b
)

echo.
echo ========================================
echo   INFORMACION DE ACCESO
echo ========================================
echo.
echo Tu IP local: %IP%
echo.
echo En tu CELULAR:
echo   1. Conectate a la misma red WiFi
echo   2. Abre el navegador (Chrome/Safari)
echo   3. Ingresa esta URL:
echo.
echo   http://%IP%:8000
echo.
echo ========================================
echo.

:: Activar entorno virtual si existe
if exist "venv\Scripts\activate.bat" (
    echo [2/4] Activando entorno virtual...
    call venv\Scripts\activate
    echo OK
    echo.
) else (
    echo [2/4] No se encontro entorno virtual, continuando...
    echo.
)

:: Verificar si el puerto está en uso
echo [3/4] Verificando puerto 8000...
netstat -ano | findstr :8000 >nul
if %errorlevel% == 0 (
    echo.
    echo ADVERTENCIA: El puerto 8000 esta en uso
    echo.
    set /p continuar="Deseas continuar? (S/N): "
    if /i not "%continuar%"=="S" (
        echo.
        echo Operacion cancelada
        pause
        exit /b
    )
    echo.
) else (
    echo OK: Puerto disponible
    echo.
)

:: Verificar firewall (solo informativo)
echo [4/4] Verificando firewall...
echo.
echo NOTA: Si no puedes acceder desde el celular, puede ser el firewall.
echo       Ejecuta PowerShell como Administrador y ejecuta:
echo.
echo       New-NetFirewallRule -DisplayName "Django Dev" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
echo.
echo ========================================
echo   INICIANDO SERVIDOR
echo ========================================
echo.
echo Presiona Ctrl+C para detener el servidor
echo.
echo IMPORTANTE: El servidor debe decir "0.0.0.0:8000" (no 127.0.0.1:8000)
echo.

:: Iniciar servidor
python manage.py runserver 0.0.0.0:8000

pause






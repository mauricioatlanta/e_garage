@echo off
echo 📱 Iniciando eGarage para acceso móvil...
echo.

:: Obtener IP local
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set IP=%%a
    goto :found
)
:found
set IP=%IP:~1%

echo 🌐 Tu IP local es: %IP%
echo 📱 Accede desde tu celular: http://%IP%:8000
echo.
echo ⚠️  Asegúrate de que tu celular esté en la misma red Wi-Fi
echo.

:: Activar entorno virtual si existe
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate
    echo ✅ Entorno virtual activado
    echo.
)

:: Verificar si el puerto está en uso
netstat -ano | findstr :8000 >nul
if %errorlevel% == 0 (
    echo ⚠️  El puerto 8000 está en uso. ¿Deseas continuar? (S/N)
    set /p continuar=
    if /i not "%continuar%"=="S" (
        echo ❌ Operación cancelada
        pause
        exit /b
    )
)

echo 🚀 Iniciando servidor Django...
echo.
python manage.py runserver 0.0.0.0:8000

pause

















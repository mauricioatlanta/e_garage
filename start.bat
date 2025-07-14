@echo off
echo 🚗 Iniciando TallerPro...

:: Verificar entorno virtual
if not exist "venv\Scripts\activate.bat" (
    echo ❌ No se encontró el entorno virtual en venv\Scripts\activate.bat
    pause
    exit /b
)

:: Activar entorno virtual
call venv\Scripts\activate

:: Abrir navegador por defecto apuntando al servidor local
start http://127.0.0.1:8000/

:: Iniciar el servidor Django
python manage.py runserver || (
    echo ❌ Error al iniciar el servidor Django.
    pause
    exit /b
)

pause

@echo off
echo 🚀 Iniciando configuración inicial de TallerPro...

:: Activar entorno virtual
echo ✅ Activando entorno virtual...
call venv\Scripts\activate

:: Instalar dependencias
echo 📦 Instalando librerías desde requirements.txt...
pip install -r requirements.txt

:: Aplicar migraciones
echo 📄 Aplicando migraciones...
python manage.py migrate

:: Iniciar servidor
echo 🌐 Ejecutando servidor Django...
python manage.py runserver

pause

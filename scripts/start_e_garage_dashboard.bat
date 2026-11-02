@echo off
cd /d %~dp0
cd e_garage
echo 🟢 Ejecutando proyecto limpio desde: %cd%
python manage.py runserver
pause

#!/bin/bash
# ============================================================
# 🚀 SCRIPT DE CONFIGURACIÓN AUTOMÁTICA PARA PYTHONANYWHERE
# ============================================================
# Archivo: setup_pythonanywhere.sh
# Ejecutar en consola de PythonAnywhere después de clonar el repo

echo "🚀 Iniciando configuración automática de eGarage en PythonAnywhere..."

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Función para imprimir status
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 1. Verificar que estamos en el directorio correcto
if [ ! -f "manage.py" ]; then
    print_error "No se encontró manage.py. Asegúrate de estar en el directorio del proyecto."
    exit 1
fi

print_status "Directorio del proyecto verificado"

# 2. Activar virtualenv
echo "🔧 Activando virtualenv..."
source ~/.virtualenvs/venv_egarage/bin/activate

if [ $? -eq 0 ]; then
    print_status "Virtualenv activado"
else
    print_warning "Virtualenv no encontrado. Creando nuevo..."
    mkvirtualenv --python=/usr/bin/python3.11 venv_egarage
    workon venv_egarage
fi

# 3. Instalar dependencias
echo "📦 Instalando dependencias..."
pip install -r requirements_pythonanywhere.txt

if [ $? -eq 0 ]; then
    print_status "Dependencias instaladas"
else
    print_error "Error instalando dependencias"
    exit 1
fi

# 4. Crear archivo .env si no existe
if [ ! -f ".env" ]; then
    echo "🔐 Creando archivo .env..."
    cat > .env << EOF
DJANGO_SECRET_KEY=laila2013-production-key-change-in-server
DB_NAME=atlantareciclajes\$egarage
DB_USER=atlantareciclajes
DB_PASSWORD=laila2013
DB_HOST=atlantareciclajes.mysql.pythonanywhere-services.com
DB_PORT=3306
EOF
    print_status "Archivo .env creado"
else
    print_status "Archivo .env ya existe"
fi

# 5. Crear directorios necesarios
echo "📁 Creando directorios necesarios..."
mkdir -p staticfiles
mkdir -p media
mkdir -p logs

chmod 755 staticfiles
chmod 755 media
chmod 755 logs

print_status "Directorios creados"

# 6. Ejecutar migraciones
echo "🗄️  Ejecutando migraciones..."
python manage.py migrate --settings=e_garage.settings_production

if [ $? -eq 0 ]; then
    print_status "Migraciones completadas"
else
    print_error "Error en migraciones"
    exit 1
fi

# 7. Recopilar archivos estáticos
echo "🎨 Recopilando archivos estáticos..."
python manage.py collectstatic --noinput --settings=e_garage.settings_production

if [ $? -eq 0 ]; then
    print_status "Archivos estáticos recopilados"
else
    print_error "Error recopilando archivos estáticos"
    exit 1
fi

# 8. Verificar configuración
echo "🔍 Verificando configuración..."
python manage.py check --settings=e_garage.settings_production

if [ $? -eq 0 ]; then
    print_status "Configuración verificada"
else
    print_warning "Advertencias en la configuración"
fi

# 9. Mostrar resumen
echo ""
echo "🎉 ¡Configuración completada!"
echo "==============================================="
echo "✅ Virtualenv: venv_egarage"
echo "✅ Dependencias: Instaladas"
echo "✅ Base de datos: Migrada"
echo "✅ Archivos estáticos: Recopilados"
echo "✅ Configuración: Verificada"
echo ""
echo "📋 PRÓXIMOS PASOS:"
echo "1. Configurar archivo WSGI en el dashboard web"
echo "2. Configurar rutas de archivos estáticos"
echo "3. Crear superusuario:"
echo "   python manage.py createsuperuser --settings=e_garage.settings_production"
echo "4. Reiniciar aplicación web:"
echo "   touch /var/www/atlantareciclajes_pythonanywhere_com_wsgi.py"
echo ""
echo "🌐 URL: https://e-garage-atlantareciclajes.pythonanywhere.com"
echo "==============================================="

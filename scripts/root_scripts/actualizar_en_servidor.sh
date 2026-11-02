#!/bin/bash
# Script para ejecutar EN EL SERVIDOR
# Copiar este archivo al servidor y ejecutar: bash actualizar_en_servidor.sh

set -e

echo "=========================================="
echo "🔄 ACTUALIZANDO SERVIDOR eGARAGE"
echo "=========================================="
echo ""

# Variables
PROJECT_DIR="/home/atlantareciclajes/apps/egarage/current"
VENV_PATH="/home/atlantareciclajes/.virtualenvs/venv_egarage310"

# Ir al directorio del proyecto
cd "$PROJECT_DIR" || {
    echo "❌ Error: No se puede acceder a $PROJECT_DIR"
    exit 1
}

echo "📁 Directorio: $(pwd)"
echo ""

# Activar virtualenv
echo "🔧 Activando virtualenv..."
source "$VENV_PATH/bin/activate" || {
    echo "❌ Error: No se puede activar virtualenv"
    exit 1
}

# Verificar Git
echo "📥 Actualizando código desde Git..."
git pull origin main || {
    echo "⚠️  Error al hacer git pull, continuando con archivos existentes..."
}

# Instalar dependencias
echo ""
echo "📦 Instalando/actualizando dependencias..."
pip install -r requirements.txt --quiet --upgrade

# Ejecutar migraciones
echo ""
echo "🗄️  Ejecutando migraciones..."
python manage.py migrate --noinput

# Recopilar estáticos
echo ""
echo "📁 Recopilando archivos estáticos..."
python manage.py collectstatic --noinput

# Arreglar testuser_usa
echo ""
echo "🔧 Verificando/arreglando usuario testuser_usa..."
if python manage.py fix_testuser_usa 2>/dev/null; then
    echo "✅ Usuario testuser_usa actualizado"
else
    echo "⚠️  Comando fix_testuser_usa no disponible (ejecutar manualmente)"
fi

# Verificar sistema
echo ""
echo "✅ Verificando sistema..."
python manage.py check || {
    echo "⚠️  Advertencias encontradas en 'check', pero continuando..."
}

# Reiniciar aplicación
echo ""
echo "🔄 Reiniciando aplicación web..."
touch /var/www/atlantareciclajes_digitalocean_com_wsgi.py 2>/dev/null || {
    echo "⚠️  No se pudo tocar archivo WSGI (puede requerir permisos)"
    echo "   Reiniciar manualmente desde el dashboard de DigitalOcean"
}

echo ""
echo "=========================================="
echo "✅ ACTUALIZACIÓN COMPLETADA"
echo "=========================================="
echo ""
echo "📋 Verificar:"
echo "   1. Logs: tail -f ~/logs/user/error.log"
echo "   2. Sitio: https://www.egarage.cl/"
echo "   3. Login testuser_usa: https://www.egarage.cl/us/accounts/login/"
echo ""
echo "🔑 Credenciales testuser_usa:"
echo "   Usuario: testuser_usa"
echo "   Contraseña: TestUSA2025!"
echo ""


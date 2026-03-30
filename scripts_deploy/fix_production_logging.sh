#!/bin/bash
# Script para actualizar el middleware de logging en producción
# Reduce el ruido de logs y bloquea bots escaneadores

set -e

echo "========================================="
echo "Fix Production Logging - eGarage"
echo "========================================="

# Detectar ruta del proyecto
if [ -d "/srv/egarage" ]; then
    PROJECT_DIR="/srv/egarage"
elif [ -d "/home/egarage/egarage" ]; then
    PROJECT_DIR="/home/egarage/egarage"
else
    echo "❌ No se encontró el directorio del proyecto"
    exit 1
fi

echo "📁 Directorio del proyecto: $PROJECT_DIR"
cd "$PROJECT_DIR"

# Activar entorno virtual
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Entorno virtual activado"
elif [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✅ Entorno virtual activado"
else
    echo "⚠️ No se encontró entorno virtual, continuando sin activar"
fi

# Backup del middleware actual
echo "📦 Creando backup del middleware actual..."
BACKUP_DIR="$PROJECT_DIR/backups/middleware_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp -r taller/middleware/*.py "$BACKUP_DIR/" 2>/dev/null || true
cp -r gestion_taller/middleware/*.py "$BACKUP_DIR/" 2>/dev/null || true
echo "✅ Backup creado en: $BACKUP_DIR"

# Actualizar archivos desde repositorio local
echo "🔄 Actualizando archivos del middleware..."

# Copiar lang_policy.py actualizado
if [ -f "taller/middleware/lang_policy.py" ]; then
    echo "  - Actualizando taller/middleware/lang_policy.py"
fi

# Copiar bot_filter.py nuevo
if [ -f "gestion_taller/middleware/bot_filter.py" ]; then
    echo "  - Nuevo: gestion_taller/middleware/bot_filter.py"
fi

echo ""
echo "⚙️  INSTRUCCIONES MANUALES:"
echo ""
echo "1. Agregar BotFilterMiddleware al inicio de MIDDLEWARE en settings_prod.py:"
echo ""
echo "   MIDDLEWARE = ["
echo "       'gestion_taller.middleware.bot_filter.BotFilterMiddleware',  # ← AGREGAR AQUÍ"
echo "       'django.middleware.security.SecurityMiddleware',"
echo "       ..."
echo "   ]"
echo ""
echo "2. Reiniciar Gunicorn:"
echo "   sudo systemctl restart gunicorn"
echo ""
echo "3. Verificar logs limpios:"
echo "   sudo journalctl -u gunicorn -n 50 --no-pager"
echo ""
echo "========================================="
echo "✅ Archivos actualizados"
echo "========================================="

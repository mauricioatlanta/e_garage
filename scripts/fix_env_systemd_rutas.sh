#!/bin/bash
# Script para corregir rutas placeholder en .env.systemd
# Ejecutar en el servidor: sudo bash fix_env_systemd_rutas.sh

set -e

echo "=========================================="
echo "🔍 Buscando y corrigiendo rutas en .env.systemd"
echo "=========================================="
echo ""

# 1. Buscar archivo .env.systemd
echo "[1] Buscando archivo .env.systemd..."
echo ""

# Buscar en ubicaciones comunes
ENV_FILES=(
    "/etc/systemd/system/egarage-gunicorn.service.d/.env.systemd"
    "/srv/egarage/.env.systemd"
    "/opt/egarage/.env.systemd"
    "/var/www/egarage/.env.systemd"
)

# También buscar referencias en el servicio systemd
SERVICE_FILE="/etc/systemd/system/egarage-gunicorn.service"
if [ -f "$SERVICE_FILE" ]; then
    ENV_FILE_REF=$(sudo grep -i "EnvironmentFile" "$SERVICE_FILE" | awk '{print $2}' | head -1)
    if [ -n "$ENV_FILE_REF" ]; then
        ENV_FILES+=("$ENV_FILE_REF")
    fi
fi

ENV_FILE=""
for file in "${ENV_FILES[@]}"; do
    if [ -f "$file" ]; then
        ENV_FILE="$file"
        break
    fi
done

# Si no se encontró, buscar recursivamente
if [ -z "$ENV_FILE" ]; then
    echo "Buscando en todo el sistema..."
    ENV_FILE=$(sudo find /etc/systemd /srv /opt /var/www -name ".env.systemd" -type f 2>/dev/null | head -1)
fi

if [ -z "$ENV_FILE" ]; then
    echo "❌ No se encontró archivo .env.systemd"
    echo ""
    echo "Ubicaciones buscadas:"
    for file in "${ENV_FILES[@]}"; do
        echo "   - $file"
    done
    echo ""
    echo "Por favor, indica la ruta del archivo .env.systemd:"
    read -p "Ruta: " ENV_FILE
    if [ ! -f "$ENV_FILE" ]; then
        echo "❌ El archivo no existe: $ENV_FILE"
        exit 1
    fi
fi

echo "✅ Archivo encontrado: $ENV_FILE"
echo ""

# 2. Verificar rutas placeholder
echo "[2] Verificando rutas placeholder..."
echo ""

HAS_PLACEHOLDER=false
if sudo grep -q "STATIC_ROOT=/ruta/a/staticfiles" "$ENV_FILE"; then
    echo "❌ STATIC_ROOT tiene ruta placeholder"
    HAS_PLACEHOLDER=true
fi

if sudo grep -q "MEDIA_ROOT=/ruta/a/media" "$ENV_FILE"; then
    echo "❌ MEDIA_ROOT tiene ruta placeholder"
    HAS_PLACEHOLDER=true
fi

if [ "$HAS_PLACEHOLDER" = false ]; then
    echo "✅ No se encontraron rutas placeholder"
    echo ""
    echo "Rutas actuales:"
    sudo grep -E "^(STATIC_ROOT|MEDIA_ROOT)=" "$ENV_FILE" || echo "  (no encontradas)"
    exit 0
fi

# 3. Determinar rutas de producción
echo "[3] Configurando rutas de producción..."
echo ""

# Intentar detectar el directorio del proyecto
PROJECT_DIR=""
if [ -d "/srv/egarage" ]; then
    PROJECT_DIR="/srv/egarage"
elif [ -d "/opt/egarage" ]; then
    PROJECT_DIR="/opt/egarage"
elif [ -d "/var/www/egarage" ]; then
    PROJECT_DIR="/var/www/egarage"
else
    echo "No se pudo detectar el directorio del proyecto."
    read -p "Ingresa el directorio del proyecto (ej: /srv/egarage): " PROJECT_DIR
fi

STATIC_ROOT="${PROJECT_DIR}/staticfiles"
MEDIA_ROOT="${PROJECT_DIR}/media"

echo "Rutas propuestas:"
echo "   STATIC_ROOT=$STATIC_ROOT"
echo "   MEDIA_ROOT=$MEDIA_ROOT"
echo ""

read -p "¿Usar estas rutas? (s/n): " CONFIRM
if [ "$CONFIRM" != "s" ] && [ "$CONFIRM" != "S" ]; then
    read -p "STATIC_ROOT: " STATIC_ROOT
    read -p "MEDIA_ROOT: " MEDIA_ROOT
fi

# 4. Crear backup
echo ""
echo "[4] Creando backup..."
BACKUP_FILE="${ENV_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
sudo cp "$ENV_FILE" "$BACKUP_FILE"
echo "✅ Backup creado: $BACKUP_FILE"

# 5. Crear directorios
echo ""
echo "[5] Creando directorios..."
sudo mkdir -p "$STATIC_ROOT"
sudo mkdir -p "$MEDIA_ROOT"
echo "✅ Directorios creados"

# 6. Configurar permisos
echo ""
echo "[6] Configurando permisos..."

# Detectar usuario del servicio
SERVICE_USER=$(sudo systemctl show egarage-gunicorn | grep "^User=" | cut -d= -f2 || echo "egarage")
SERVICE_GROUP=$(sudo systemctl show egarage-gunicorn | grep "^Group=" | cut -d= -f2 || echo "www-data")

if [ -z "$SERVICE_USER" ]; then
    SERVICE_USER="egarage"
fi
if [ -z "$SERVICE_GROUP" ]; then
    SERVICE_GROUP="www-data"
fi

echo "Usuario del servicio: $SERVICE_USER"
echo "Grupo: $SERVICE_GROUP"

sudo chown -R "$SERVICE_USER:$SERVICE_GROUP" "$STATIC_ROOT"
sudo chown -R "$SERVICE_USER:$SERVICE_GROUP" "$MEDIA_ROOT"
sudo chmod -R 755 "$STATIC_ROOT"
sudo chmod -R 775 "$MEDIA_ROOT"

echo "✅ Permisos configurados"

# 7. Actualizar .env.systemd
echo ""
echo "[7] Actualizando .env.systemd..."

TEMP_FILE=$(mktemp)
sudo cp "$ENV_FILE" "$TEMP_FILE"

# Reemplazar rutas placeholder
sudo sed -i "s|STATIC_ROOT=/ruta/a/staticfiles|STATIC_ROOT=$STATIC_ROOT|g" "$TEMP_FILE"
sudo sed -i "s|MEDIA_ROOT=/ruta/a/media|MEDIA_ROOT=$MEDIA_ROOT|g" "$TEMP_FILE"

# Si las variables no existen, agregarlas
if ! sudo grep -q "^STATIC_ROOT=" "$TEMP_FILE"; then
    echo "STATIC_ROOT=$STATIC_ROOT" | sudo tee -a "$TEMP_FILE" > /dev/null
fi

if ! sudo grep -q "^MEDIA_ROOT=" "$TEMP_FILE"; then
    echo "MEDIA_ROOT=$MEDIA_ROOT" | sudo tee -a "$TEMP_FILE" > /dev/null
fi

sudo mv "$TEMP_FILE" "$ENV_FILE"
echo "✅ Archivo actualizado"

# 8. Verificar cambios
echo ""
echo "[8] Verificando cambios..."
echo ""
echo "Rutas actualizadas:"
sudo grep -E "^(STATIC_ROOT|MEDIA_ROOT)=" "$ENV_FILE"

# 9. Recargar servicio
echo ""
echo "[9] Recargando servicio..."
sudo systemctl daemon-reload
sudo systemctl restart egarage-gunicorn
echo "✅ Servicio recargado"

# 10. Verificar estado
echo ""
echo "[10] Verificando estado del servicio..."
sudo systemctl status egarage-gunicorn --no-pager -l | head -20

echo ""
echo "=========================================="
echo "✅ Corrección completada"
echo "=========================================="
echo ""
echo "📝 Próximos pasos:"
echo "   1. Recolectar archivos estáticos:"
echo "      cd $PROJECT_DIR"
echo "      source venv/bin/activate  # si usas venv"
echo "      python manage.py collectstatic --noinput"
echo ""
echo "   2. Verificar que Nginx apunta a las mismas rutas"
echo "   3. Probar el sitio web"

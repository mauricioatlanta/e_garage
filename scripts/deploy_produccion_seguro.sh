#!/bin/bash
# Script de despliegue seguro que excluye código fuente del core de IA
# Uso: ./scripts/deploy_produccion_seguro.sh [directorio_destino]

set -e  # Salir si hay errores

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================="
echo "🔒 DESPLIEGUE SEGURO - EGARAGE"
echo "==========================================${NC}\n"

# Directorio de destino (por defecto: deploy/)
DEST_DIR=${1:-deploy}

# Verificar que el código está ofuscado
if [ ! -d "taller/utils/motor_ia_core_compiled" ]; then
    echo -e "${RED}❌ ERROR: Código ofuscado no encontrado${NC}"
    echo -e "${YELLOW}⚠️  Ejecuta primero: python scripts/ofuscar_motor_ia.py${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Código ofuscado encontrado${NC}\n"

# Crear directorio de despliegue
echo -e "${BLUE}[1/5]${NC} Creando directorio de despliegue..."
mkdir -p "$DEST_DIR"
rm -rf "$DEST_DIR"/*

# Copiar archivos del proyecto (excluyendo código fuente del core)
echo -e "${BLUE}[2/5]${NC} Copiando archivos del proyecto..."

# Copiar todo excepto el código fuente del core
rsync -av --exclude='motor_ia_core.py' \
          --exclude='motor_ia_core_compiled/' \
          --exclude='__pycache__/' \
          --exclude='*.pyc' \
          --exclude='.git/' \
          --exclude='venv/' \
          --exclude='.venv/' \
          --exclude='node_modules/' \
          --exclude='*.log' \
          --exclude='db.sqlite3' \
          . "$DEST_DIR/" || {
    echo -e "${YELLOW}⚠️  rsync no disponible, usando cp...${NC}"
    # Fallback si rsync no está disponible
    find . -type f -name "*.py" ! -path "./venv/*" ! -path "./.venv/*" ! -path "./node_modules/*" ! -name "motor_ia_core.py" | \
    while read file; do
        dest_file="$DEST_DIR/$file"
        mkdir -p "$(dirname "$dest_file")"
        cp "$file" "$dest_file"
    done
}

# Copiar código ofuscado
echo -e "${BLUE}[3/5]${NC} Copiando código ofuscado..."
cp -r taller/utils/motor_ia_core_compiled "$DEST_DIR/taller/utils/"

# Verificar que el código fuente NO está en el despliegue
echo -e "${BLUE}[4/5]${NC} Verificando seguridad..."

if [ -f "$DEST_DIR/taller/utils/motor_ia_core.py" ]; then
    echo -e "${RED}❌ ERROR CRÍTICO: Código fuente encontrado en despliegue${NC}"
    echo -e "${RED}   El archivo motor_ia_core.py NO debe estar en producción${NC}"
    rm -f "$DEST_DIR/taller/utils/motor_ia_core.py"
    echo -e "${YELLOW}⚠️  Archivo eliminado automáticamente${NC}"
fi

# Verificar que el código ofuscado SÍ está
if [ ! -d "$DEST_DIR/taller/utils/motor_ia_core_compiled" ]; then
    echo -e "${RED}❌ ERROR: Código ofuscado no encontrado en despliegue${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Verificación de seguridad completada${NC}"

# Crear archivo de verificación
echo -e "${BLUE}[5/5]${NC} Creando archivo de verificación..."
cat > "$DEST_DIR/DEPLOY_INFO.txt" << EOF
Despliegue Seguro de eGarage
Fecha: $(date)
Versión: $(git rev-parse --short HEAD 2>/dev/null || echo "N/A")

✅ Código fuente del core de IA EXCLUIDO
✅ Código ofuscado INCLUIDO
✅ Listo para producción

IMPORTANTE:
- NO contiene motor_ia_core.py (código fuente)
- SÍ contiene motor_ia_core_compiled/ (código ofuscado)
- El wrapper motor_ia.py importará automáticamente el código ofuscado
EOF

echo -e "\n${GREEN}=========================================="
echo "✅ DESPLIEGUE COMPLETADO"
echo "==========================================${NC}\n"

echo -e "${BLUE}📦 Directorio de despliegue:${NC} $DEST_DIR"
echo -e "${BLUE}📄 Información:${NC} $DEST_DIR/DEPLOY_INFO.txt\n"

echo -e "${YELLOW}⚠️  RECORDATORIO:${NC}"
echo "   - Verifica que motor_ia_core.py NO está en $DEST_DIR"
echo "   - Verifica que motor_ia_core_compiled/ SÍ está en $DEST_DIR"
echo "   - Ejecuta tests en el servidor antes de activar\n"




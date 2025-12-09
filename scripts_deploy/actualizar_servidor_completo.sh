#!/bin/bash
# ============================================================================
# Script de Actualización Completa del Servidor eGarage
# ============================================================================
# Este script actualiza completamente el servidor con la versión nueva
# SIN BORRAR datos de suscriptores ni información de clientes
#
# IMPORTANTE: Ejecutar DESPUÉS de hacer backup con backup_datos_criticos.py
# ============================================================================

set -e  # Salir si hay algún error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
PROJECT_DIR="/home/atlantareciclajes/apps/egarage/current"
VENV_NAME="venv_egarage310"
BACKUP_DIR="$PROJECT_DIR/backups/actualizacion_$(date +%Y%m%d_%H%M%S)"

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}🚀 ACTUALIZACIÓN COMPLETA DEL SERVIDOR eGarage${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "$PROJECT_DIR/manage.py" ]; then
    echo -e "${RED}❌ ERROR: No se encuentra manage.py en $PROJECT_DIR${NC}"
    echo "   Verifica que estás en el directorio correcto del proyecto."
    exit 1
fi

cd "$PROJECT_DIR"

# ============================================================================
# PASO 1: VERIFICAR BACKUP
# ============================================================================
echo -e "${YELLOW}📋 PASO 1: Verificando backup de datos críticos...${NC}"
if [ ! -d "$PROJECT_DIR/backups/datos_criticos" ]; then
    echo -e "${RED}❌ ERROR: No se encontró directorio de backups.${NC}"
    echo "   Ejecuta primero: python scripts_deploy/backup_datos_criticos.py"
    exit 1
fi

ULTIMO_BACKUP=$(ls -td "$PROJECT_DIR/backups/datos_criticos/backup_completo_"* 2>/dev/null | head -1)
if [ -z "$ULTIMO_BACKUP" ]; then
    echo -e "${RED}❌ ERROR: No se encontró ningún backup reciente.${NC}"
    echo "   Ejecuta primero: python scripts_deploy/backup_datos_criticos.py"
    exit 1
fi

echo -e "${GREEN}✅ Backup encontrado: $ULTIMO_BACKUP${NC}"
echo ""

# ============================================================================
# PASO 2: CREAR BACKUP ADICIONAL DE BASE DE DATOS
# ============================================================================
echo -e "${YELLOW}📋 PASO 2: Creando backup adicional de base de datos...${NC}"
mkdir -p "$BACKUP_DIR"

DB_PATH=$(python -c "import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings'); django.setup(); from django.conf import settings; print(settings.DATABASES['default']['NAME'])")

if [ -f "$DB_PATH" ]; then
    cp "$DB_PATH" "$BACKUP_DIR/db_backup_$(date +%Y%m%d_%H%M%S).sqlite3"
    echo -e "${GREEN}✅ Backup de base de datos creado${NC}"
else
    echo -e "${YELLOW}⚠️  Base de datos no encontrada en ruta esperada${NC}"
fi
echo ""

# ============================================================================
# PASO 3: ACTIVAR ENTORNO VIRTUAL
# ============================================================================
echo -e "${YELLOW}📋 PASO 3: Activando entorno virtual...${NC}"
if [ -d "$HOME/.virtualenvs/$VENV_NAME" ]; then
    source "$HOME/.virtualenvs/$VENV_NAME/bin/activate"
    echo -e "${GREEN}✅ Entorno virtual activado${NC}"
elif [ -d "$PROJECT_DIR/venv" ]; then
    source "$PROJECT_DIR/venv/bin/activate"
    echo -e "${GREEN}✅ Entorno virtual activado (local)${NC}"
else
    echo -e "${YELLOW}⚠️  No se encontró entorno virtual, continuando sin él...${NC}"
fi
echo ""

# ============================================================================
# PASO 4: ACTUALIZAR CÓDIGO DESDE GIT
# ============================================================================
echo -e "${YELLOW}📋 PASO 4: Actualizando código desde Git...${NC}"
echo "   Esto actualizará todos los archivos del proyecto..."

# Guardar cambios locales si existen (stash)
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}⚠️  Hay cambios locales, guardándolos en stash...${NC}"
    git stash save "Cambios locales antes de actualización $(date +%Y%m%d_%H%M%S)"
fi

# Obtener última versión
echo "   Obteniendo última versión desde Git..."
git fetch origin

# Ver qué rama estamos usando
BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "   Rama actual: $BRANCH"

# Hacer pull
git pull origin "$BRANCH"
echo -e "${GREEN}✅ Código actualizado${NC}"
echo ""

# ============================================================================
# PASO 5: ACTUALIZAR DEPENDENCIAS
# ============================================================================
echo -e "${YELLOW}📋 PASO 5: Actualizando dependencias Python...${NC}"
if [ -f "requirements.txt" ]; then
    pip install --upgrade pip
    pip install -r requirements.txt
    echo -e "${GREEN}✅ Dependencias actualizadas${NC}"
else
    echo -e "${YELLOW}⚠️  No se encontró requirements.txt${NC}"
fi
echo ""

# ============================================================================
# PASO 6: APLICAR MIGRACIONES DE BASE DE DATOS
# ============================================================================
echo -e "${YELLOW}📋 PASO 6: Aplicando migraciones de base de datos...${NC}"
echo "   Esto actualizará la estructura de la BD sin borrar datos..."

# Verificar estado de migraciones
echo "   Verificando estado de migraciones..."
python manage.py showmigrations | tail -20

# Aplicar migraciones con --fake-initial para evitar errores si las tablas ya existen
echo ""
echo "   Aplicando migraciones..."
python manage.py migrate --fake-initial
python manage.py migrate

echo -e "${GREEN}✅ Migraciones aplicadas${NC}"
echo ""

# ============================================================================
# PASO 7: RECOLECTAR ARCHIVOS ESTÁTICOS
# ============================================================================
echo -e "${YELLOW}📋 PASO 7: Recolectando archivos estáticos...${NC}"
python manage.py collectstatic --noinput
echo -e "${GREEN}✅ Archivos estáticos recolectados${NC}"
echo ""

# ============================================================================
# PASO 8: LIMPIAR CACHÉ
# ============================================================================
echo -e "${YELLOW}📋 PASO 8: Limpiando caché...${NC}"
# Limpiar pyc y __pycache__
find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
echo -e "${GREEN}✅ Caché limpiado${NC}"
echo ""

# ============================================================================
# PASO 9: VERIFICAR CONFIGURACIÓN
# ============================================================================
echo -e "${YELLOW}📋 PASO 9: Verificando configuración de Django...${NC}"
python manage.py check --deploy
echo -e "${GREEN}✅ Verificación completada${NC}"
echo ""

# ============================================================================
# PASO 10: VERIFICAR DATOS CRÍTICOS
# ============================================================================
echo -e "${YELLOW}📋 PASO 10: Verificando que los datos críticos estén intactos...${NC}"

# Contar empresas/suscriptores
EMPRESAS=$(python manage.py shell -c "from taller.models import Empresa; print(Empresa.objects.count())" 2>/dev/null || echo "0")
echo "   Empresas/Suscriptores: $EMPRESAS"

# Contar usuarios
USUARIOS=$(python manage.py shell -c "from django.contrib.auth.models import User; print(User.objects.count())" 2>/dev/null || echo "0")
echo "   Usuarios: $USUARIOS"

# Contar clientes
CLIENTES=$(python manage.py shell -c "from taller.models import Cliente; print(Cliente.objects.count())" 2>/dev/null || echo "0")
echo "   Clientes: $CLIENTES"

if [ "$EMPRESAS" -eq "0" ] && [ "$USUARIOS" -gt "0" ]; then
    echo -e "${RED}⚠️  ADVERTENCIA: Hay usuarios pero no hay empresas. Esto puede indicar un problema.${NC}"
elif [ "$EMPRESAS" -gt "0" ]; then
    echo -e "${GREEN}✅ Datos críticos verificados${NC}"
fi
echo ""

# ============================================================================
# RESUMEN FINAL
# ============================================================================
echo -e "${BLUE}============================================================================${NC}"
echo -e "${GREEN}✅ ACTUALIZACIÓN COMPLETADA${NC}"
echo -e "${BLUE}============================================================================${NC}"
echo ""
echo "📊 Resumen:"
echo "   - Código actualizado desde Git"
echo "   - Dependencias actualizadas"
echo "   - Migraciones aplicadas"
echo "   - Archivos estáticos recolectados"
echo "   - Caché limpiado"
echo ""
echo "📁 Backups guardados en:"
echo "   - $ULTIMO_BACKUP"
echo "   - $BACKUP_DIR"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANTE:${NC}"
echo "   1. Reinicia la aplicación web (reload en PythonAnywhere)"
echo "   2. Verifica que el sitio funciona correctamente"
echo "   3. Revisa los logs si hay algún problema"
echo ""
echo -e "${GREEN}🎉 ¡Actualización completada exitosamente!${NC}"
echo ""






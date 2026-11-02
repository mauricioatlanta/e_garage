#!/bin/bash

# ============================================================================
# SCRIPT DE DEPLOYMENT - eGarage v2.0
# ============================================================================
# Uso: ./deploy.sh
# Descripción: Actualiza eGarage en producción con todos los cambios
# ============================================================================

set -e  # Exit on error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════╗"
echo "║                                                         ║"
echo "║  🚀 eGarage v2.0 - DEPLOYMENT SCRIPT                   ║"
echo "║                                                         ║"
echo "╚════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ============================================================================
# 1. BACKUP
# ============================================================================

echo -e "${YELLOW}[1/10] Creando backup de la base de datos...${NC}"

BACKUP_DIR="backups/deployments"
mkdir -p $BACKUP_DIR

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_pre_deploy_$TIMESTAMP.json"

python manage.py dumpdata \
    --natural-foreign \
    --natural-primary \
    --exclude=contenttypes \
    --exclude=auth.permission \
    --exclude=sessions \
    --output=$BACKUP_FILE

if [ -f "$BACKUP_FILE" ]; then
    echo -e "${GREEN}✅ Backup creado: $BACKUP_FILE${NC}"
else
    echo -e "${RED}❌ Error creando backup${NC}"
    exit 1
fi

# ============================================================================
# 2. GIT STATUS (si aplica)
# ============================================================================

echo -e "${YELLOW}[2/10] Verificando repositorio Git...${NC}"

if [ -d ".git" ]; then
    echo "Repositorio Git detectado"
    git status --short
    echo -e "${GREEN}✅ Git status verificado${NC}"
else
    echo "No hay repositorio Git. Saltando..."
fi

# ============================================================================
# 3. VIRTUAL ENVIRONMENT
# ============================================================================

echo -e "${YELLOW}[3/10] Verificando virtual environment...${NC}"

if [ -d "venv" ]; then
    source venv/bin/activate
    echo -e "${GREEN}✅ Virtual environment activado${NC}"
else
    echo -e "${YELLOW}⚠️ Virtual environment no encontrado. Creando...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    echo -e "${GREEN}✅ Virtual environment creado y activado${NC}"
fi

# ============================================================================
# 4. DEPENDENCIAS
# ============================================================================

echo -e "${YELLOW}[4/10] Instalando/Actualizando dependencias...${NC}"

pip install --upgrade pip
pip install -r requirements.txt --upgrade

echo -e "${GREEN}✅ Dependencias instaladas${NC}"

# ============================================================================
# 5. MIGRACIONES
# ============================================================================

echo -e "${YELLOW}[5/10] Ejecutando migraciones...${NC}"

# Mostrar plan
echo "Plan de migraciones:"
python manage.py migrate --plan

# Ejecutar
python manage.py migrate

echo -e "${GREEN}✅ Migraciones aplicadas${NC}"

# ============================================================================
# 6. ARCHIVOS ESTÁTICOS
# ============================================================================

echo -e "${YELLOW}[6/10] Colectando archivos estáticos...${NC}"

python manage.py collectstatic --noinput --clear

echo -e "${GREEN}✅ Archivos estáticos colectados${NC}"

# ============================================================================
# 7. TRADUCCIONES
# ============================================================================

echo -e "${YELLOW}[7/10] Compilando traducciones...${NC}"

python manage.py compilemessages

echo -e "${GREEN}✅ Traducciones compiladas${NC}"

# ============================================================================
# 8. COMANDOS DE INICIALIZACIÓN (SOLO PRIMERA VEZ)
# ============================================================================

echo -e "${YELLOW}[8/10] Verificando inicialización...${NC}"

if [ ! -f ".deployed" ]; then
    echo -e "${BLUE}Primera instalación detectada. Ejecutando comandos iniciales...${NC}"
    
    # Cargar ubicaciones (solo si no existen)
    echo "Cargando estados y ciudades..."
    python manage.py cargar_estados_brasil || echo "⚠️ Estados Brasil ya cargados o error"
    python manage.py cargar_estados_venezuela || echo "⚠️ Estados Venezuela ya cargados o error"
    python manage.py cargar_estados_peru || echo "⚠️ Estados Perú ya cargados o error"
    
    # Cargar políticas de impuestos
    echo "Cargando políticas de impuestos..."
    python manage.py seed_tax || echo "⚠️ Tax policies ya cargadas o error"
    
    # Marcar como desplegado
    echo "v2.0 - $(date +%Y-%m-%d\ %H:%M:%S)" > .deployed
    
    echo -e "${GREEN}✅ Comandos iniciales ejecutados${NC}"
else
    echo "Sistema ya desplegado anteriormente. Saltando comandos iniciales."
    echo "Última versión desplegada:"
    cat .deployed
fi

# ============================================================================
# 9. VERIFICACIONES
# ============================================================================

echo -e "${YELLOW}[9/10] Ejecutando verificaciones...${NC}"

# System check
python manage.py check

echo -e "${GREEN}✅ Verificaciones completadas${NC}"

# ============================================================================
# 10. REINICIAR SERVICIOS (si están configurados)
# ============================================================================

echo -e "${YELLOW}[10/10] Reiniciando servicios...${NC}"

# Verificar si systemd está disponible (producción)
if command -v systemctl &> /dev/null; then
    echo "Reiniciando Gunicorn..."
    sudo systemctl restart gunicorn-egarage || echo "⚠️ Gunicorn no configurado o error"
    
    echo "Recargando Nginx..."
    sudo systemctl reload nginx || echo "⚠️ Nginx no configurado o error"
    
    echo -e "${GREEN}✅ Servicios reiniciados${NC}"
else
    echo -e "${YELLOW}⚠️ systemctl no disponible. Saltando reinicio de servicios.${NC}"
    echo -e "${YELLOW}   (Esto es normal en desarrollo Windows)${NC}"
fi

# ============================================================================
# FINALIZADO
# ============================================================================

echo ""
echo -e "${GREEN}"
echo "╔════════════════════════════════════════════════════════╗"
echo "║                                                         ║"
echo "║  🎉 DEPLOYMENT COMPLETADO EXITOSAMENTE                 ║"
echo "║                                                         ║"
echo "║  Versión: 2.0.0                                        ║"
echo "║  Fecha: $(date +%Y-%m-%d\ %H:%M:%S)                    ║"
echo "║                                                         ║"
echo "║  ✅ Backup creado                                      ║"
echo "║  ✅ Dependencias actualizadas                          ║"
echo "║  ✅ Migraciones aplicadas                              ║"
echo "║  ✅ Estáticos colectados                               ║"
echo "║  ✅ Traducciones compiladas                            ║"
echo "║  ✅ Sistema verificado                                 ║"
echo "║                                                         ║"
echo "║  🚀 eGarage v2.0 ACTUALIZADO                           ║"
echo "║                                                         ║"
echo "╚════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Verificar que el sitio responda (si está en producción)
if command -v curl &> /dev/null; then
    echo -e "${YELLOW}Verificando sitio web...${NC}"
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/ || echo "000")
    
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "302" ]; then
        echo -e "${GREEN}✅ Sitio respondiendo correctamente (HTTP $HTTP_CODE)${NC}"
    else
        echo -e "${RED}⚠️ Sitio no responde o error (HTTP $HTTP_CODE)${NC}"
        echo -e "${YELLOW}   Revisa los logs:${NC}"
        echo -e "${YELLOW}   - tail -f logs/django.log${NC}"
        echo -e "${YELLOW}   - sudo journalctl -u gunicorn-egarage -f${NC}"
    fi
fi

echo ""
echo -e "${BLUE}Deployment finalizado.${NC}"
echo -e "${BLUE}Para ver logs: tail -f logs/django.log${NC}"
echo ""

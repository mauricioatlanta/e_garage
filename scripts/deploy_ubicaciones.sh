#!/bin/bash
# ============================================================================
# SCRIPT DE DEPLOYMENT - Sistema de Ubicaciones Multi-País
# ============================================================================
# Descripción: Ejecuta deployment del sistema de ubicaciones en servidor
# Uso: bash scripts/deploy_ubicaciones.sh
# Ejecutar EN EL SERVIDOR después de git pull
# ============================================================================

set -e  # Exit on error

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Banner
echo -e "${BLUE}"
cat << "EOF"
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    DEPLOYMENT - Sistema de Ubicaciones Multi-País           ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Verificar que estamos en el directorio correcto
if [ ! -f "manage.py" ]; then
    echo -e "${RED}Error: Este script debe ejecutarse desde la raíz del proyecto${NC}"
    exit 1
fi

echo -e "${GREEN}Iniciando deployment...${NC}\n"

# ============================================================================
# PASO 1: VERIFICAR MODELOS
# ============================================================================

echo -e "${BLUE}[1/6] Verificando modelos...${NC}"

python manage.py check || {
    echo -e "${RED}Error en verificación de modelos${NC}"
    exit 1
}

echo -e "${GREEN}✅ Modelos verificados${NC}\n"

# ============================================================================
# PASO 2: VERIFICAR SI YA HAY DATOS
# ============================================================================

echo -e "${BLUE}[2/6] Verificando datos existentes...${NC}"

# Ejecutar verificación silenciosa
python manage.py verificar_ubicaciones > /tmp/ubicaciones_check.txt 2>&1 || true

# Mostrar resumen
grep "Total estados/regiones:" /tmp/ubicaciones_check.txt || echo "  • Sin datos previos"

echo ""

# ============================================================================
# PASO 3: CARGAR UBICACIONES
# ============================================================================

echo -e "${BLUE}[3/6] Cargando ubicaciones...${NC}"
echo -e "${YELLOW}Esto puede tomar 2-5 minutos${NC}\n"

# Usar --skip-existing para no duplicar en caso de re-deployment
if python manage.py cargar_todas_ubicaciones --skip-existing; then
    echo -e "\n${GREEN}✅ Ubicaciones cargadas${NC}"
else
    echo -e "\n${RED}Error cargando ubicaciones${NC}"
    exit 1
fi

# ============================================================================
# PASO 4: VERIFICAR DATOS CARGADOS
# ============================================================================

echo -e "\n${BLUE}[4/6] Verificando datos cargados...${NC}\n"

python manage.py verificar_ubicaciones > /tmp/ubicaciones_final.txt

# Mostrar resumen
grep -A 8 "COBERTURA POR PAIS:" /tmp/ubicaciones_final.txt | tail -9 || echo "Ver /tmp/ubicaciones_final.txt"

# ============================================================================
# PASO 5: BACKFILL DE CLIENTES (OPCIONAL)
# ============================================================================

echo -e "\n${BLUE}[5/6] Migración de clientes a billing_address...${NC}"

# Verificar si hay clientes sin billing_address
CLIENTES_SIN_ADDRESS=$(python manage.py shell -c "from taller.models.clientes import Cliente; print(Cliente.objects.filter(billing_address__isnull=True).count())" 2>/dev/null || echo "0")

if [ "$CLIENTES_SIN_ADDRESS" -gt 0 ]; then
    echo -e "${YELLOW}Se encontraron $CLIENTES_SIN_ADDRESS clientes sin billing_address${NC}"
    
    # Ejecutar dry-run
    echo "Ejecutando preview (dry-run)..."
    python manage.py backfill_addresses --dry-run
    
    echo ""
    read -p "¿Proceder con la migración real? (s/n): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[SsYy]$ ]]; then
        python manage.py backfill_addresses
        echo -e "${GREEN}✅ Clientes migrados${NC}"
    else
        echo -e "${YELLOW}⚠️  Migración omitida${NC}"
    fi
else
    echo -e "${GREEN}✅ No hay clientes pendientes de migración${NC}"
fi

# ============================================================================
# PASO 6: RESTART DEL SERVIDOR (OPCIONAL)
# ============================================================================

echo -e "\n${BLUE}[6/6] Restart del servidor...${NC}"

# Detectar sistema de deployment
if command -v systemctl &> /dev/null && systemctl is-active --quiet gunicorn; then
    echo "Reiniciando Gunicorn..."
    sudo systemctl restart gunicorn
    echo -e "${GREEN}✅ Gunicorn reiniciado${NC}"
elif command -v supervisorctl &> /dev/null; then
    echo "Reiniciando con Supervisor..."
    sudo supervisorctl restart egarage
    echo -e "${GREEN}✅ Supervisor reiniciado${NC}"
else
    echo -e "${YELLOW}⚠️  No se detectó Gunicorn ni Supervisor${NC}"
    echo "Reinicia manualmente tu servidor web"
fi

# ============================================================================
# RESUMEN FINAL
# ============================================================================

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                              ║${NC}"
echo -e "${GREEN}║    ✅ DEPLOYMENT COMPLETADO EXITOSAMENTE                     ║${NC}"
echo -e "${GREEN}║                                                              ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Mostrar estadísticas finales
echo -e "${BLUE}📊 Verificación final:${NC}"
python manage.py verificar_ubicaciones 2>&1 | grep -A 2 "RESUMEN GENERAL:" | tail -3

echo ""
echo -e "${BLUE}✅ Próximos pasos:${NC}"
echo -e "  1. Verificar en navegador: https://tudominio.com/us/en/clientes/crear/"
echo -e "  2. Probar selects dinámicos"
echo -e "  3. Probar modales '+ ADD CITY'"
echo -e "  4. Crear cliente de prueba"
echo ""

echo -e "${GREEN}🎉 Deployment completo${NC}"


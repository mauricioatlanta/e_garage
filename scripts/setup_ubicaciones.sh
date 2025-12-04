#!/bin/bash
# ============================================================================
# SCRIPT DE SETUP INICIAL - Sistema de Ubicaciones Multi-País
# ============================================================================
# Descripción: Configura el sistema de ubicaciones cargando todos los países
# Uso: ./scripts/setup_ubicaciones.sh [opciones]
# ============================================================================

set -e  # Exit on error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Banner
echo -e "${BLUE}"
cat << "EOF"
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    🌎 SISTEMA DE UBICACIONES MULTI-PAÍS                     ║
║                                                              ║
║    Setup Inicial - Carga de Estados y Ciudades              ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Verificar que estamos en el directorio correcto
if [ ! -f "manage.py" ]; then
    echo -e "${RED}❌ Error: Este script debe ejecutarse desde la raíz del proyecto${NC}"
    echo -e "${YELLOW}   (donde está manage.py)${NC}"
    exit 1
fi

# Verificar que Django está instalado
if ! python manage.py --version > /dev/null 2>&1; then
    echo -e "${RED}❌ Error: Django no está instalado o manage.py no es válido${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Verificaciones iniciales completadas${NC}\n"

# ============================================================================
# PASO 1: VERIFICAR ESTADO ACTUAL
# ============================================================================

echo -e "${BLUE}[1/4] Verificando estado actual...${NC}"

# Ejecutar verificación
python manage.py verificar_ubicaciones > /tmp/verificacion_ubicaciones.txt 2>&1 || true

# Mostrar resumen
echo -e "\n${YELLOW}Estado actual del sistema:${NC}"
grep "Total estados/regiones:" /tmp/verificacion_ubicaciones.txt || echo "  • Sin datos previos"

# Preguntar si continuar
echo ""
read -p "¿Desea continuar con la carga de ubicaciones? (s/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[SsYy]$ ]]; then
    echo -e "${YELLOW}⚠️  Setup cancelado por el usuario${NC}"
    exit 0
fi

# ============================================================================
# PASO 2: CARGA DE UBICACIONES
# ============================================================================

echo -e "\n${BLUE}[2/4] Cargando ubicaciones de todos los países...${NC}"
echo -e "${YELLOW}⏱️  Esto puede tomar 2-5 minutos${NC}\n"

# Ejecutar carga
if python manage.py cargar_todas_ubicaciones --skip-existing; then
    echo -e "\n${GREEN}✅ Carga de ubicaciones completada${NC}"
else
    echo -e "\n${RED}❌ Error durante la carga de ubicaciones${NC}"
    exit 1
fi

# ============================================================================
# PASO 3: VERIFICACIÓN POST-CARGA
# ============================================================================

echo -e "\n${BLUE}[3/4] Verificando datos cargados...${NC}"

# Ejecutar verificación
python manage.py verificar_ubicaciones > /tmp/verificacion_final.txt

# Mostrar resumen
echo -e "\n${GREEN}📊 Resumen de ubicaciones cargadas:${NC}"
grep -A 8 "🌍 COBERTURA POR PAÍS:" /tmp/verificacion_final.txt | tail -9

# ============================================================================
# PASO 4: MIGRACIÓN DE DATOS LEGACY (OPCIONAL)
# ============================================================================

echo -e "\n${BLUE}[4/4] Migración de datos legacy (opcional)...${NC}"

# Verificar si hay clientes con datos legacy
if python manage.py verificar_ubicaciones 2>&1 | grep -q "Clientes sin billing_address"; then
    echo -e "${YELLOW}⚠️  Se detectaron clientes con datos legacy${NC}"
    echo ""
    read -p "¿Desea migrar los datos legacy a billing_address? (s/n): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[SsYy]$ ]]; then
        echo -e "\n${YELLOW}Ejecutando migración (dry-run primero)...${NC}"
        
        # Dry-run
        python manage.py backfill_addresses --dry-run
        
        echo ""
        read -p "¿Proceder con la migración real? (s/n): " -n 1 -r
        echo
        
        if [[ $REPLY =~ ^[SsYy]$ ]]; then
            python manage.py backfill_addresses
            echo -e "${GREEN}✅ Migración completada${NC}"
        else
            echo -e "${YELLOW}⚠️  Migración cancelada${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Migración omitida${NC}"
        echo -e "${BLUE}💡 Puedes ejecutarla más tarde con:${NC}"
        echo -e "   ${YELLOW}python manage.py backfill_addresses${NC}"
    fi
else
    echo -e "${GREEN}✅ No hay datos legacy para migrar${NC}"
fi

# ============================================================================
# RESUMEN FINAL
# ============================================================================

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                              ║${NC}"
echo -e "${GREEN}║    ✅ SETUP COMPLETADO EXITOSAMENTE                          ║${NC}"
echo -e "${GREEN}║                                                              ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Mostrar estadísticas finales
echo -e "${BLUE}📊 Estadísticas finales:${NC}"
python manage.py verificar_ubicaciones 2>&1 | grep -A 2 "📊 RESUMEN GENERAL:" | tail -3

echo ""
echo -e "${BLUE}📚 Próximos pasos:${NC}"
echo -e "  1. ${YELLOW}Ver documentación:${NC} docs/README_UBICACIONES.md"
echo -e "  2. ${YELLOW}Guía rápida:${NC} docs/GUIA_RAPIDA_UBICACIONES.md"
echo -e "  3. ${YELLOW}Verificar en cualquier momento:${NC} python manage.py verificar_ubicaciones"
echo ""

# Crear archivo de marcador
echo "$(date '+%Y-%m-%d %H:%M:%S')" > .ubicaciones_setup_completed

echo -e "${GREEN}🎉 ¡Sistema de ubicaciones listo para usar!${NC}"


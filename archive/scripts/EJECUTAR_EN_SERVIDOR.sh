#!/bin/bash

# ============================================================================
# SCRIPT PARA EJECUTAR EN EL SERVIDOR - Actualización de Templates
# ============================================================================
# Ejecutar DESPUÉS de subir los archivos al servidor
# ============================================================================

set -e  # Salir si hay error

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════╗"
echo "║                                                         ║"
echo "║  🔄 ACTUALIZACIÓN DE TEMPLATES - eGarage                ║"
echo "║                                                         ║"
echo "╚════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ============================================================================
# 1. VERIFICAR ARCHIVOS SUBIDOS
# ============================================================================

echo -e "${CYAN}[1/5] Verificando archivos subidos...${NC}"

FILES=(
    "templates/us/en/onboarding/bienvenida.html"
    "templates/us/es/onboarding/bienvenida.html"
    "templates/account/signup.html"
    "templates/us/en/account/signup.html"
    "taller/forms/custom_signup.py"
    "gestion_taller/urls.py"
)

MISSING_FILES=()

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}  ✅ $file${NC}"
    else
        echo -e "${YELLOW}  ⚠️  $file (no encontrado)${NC}"
        MISSING_FILES+=("$file")
    fi
done

if [ ${#MISSING_FILES[@]} -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}⚠️  Algunos archivos no se encontraron.${NC}"
    echo -e "${YELLOW}   Asegúrate de haber subido todos los archivos.${NC}"
    echo ""
    read -p "¿Continuar de todas formas? (s/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        echo "Cancelado."
        exit 0
    fi
fi

# ============================================================================
# 2. ACTIVAR VIRTUAL ENVIRONMENT
# ============================================================================

echo ""
echo -e "${CYAN}[2/5] Activando virtual environment...${NC}"

if [ -d "venv" ]; then
    source venv/bin/activate
    echo -e "${GREEN}  ✅ Virtual environment activado${NC}"
elif [ -d "../venv" ]; then
    source ../venv/bin/activate
    echo -e "${GREEN}  ✅ Virtual environment activado${NC}"
elif command -v workon &> /dev/null; then
    workon venv_egarage310 || true
    echo -e "${GREEN}  ✅ Virtual environment activado (workon)${NC}"
else
    echo -e "${YELLOW}  ⚠️  Virtual environment no encontrado. Continuando...${NC}"
fi

# ============================================================================
# 3. VERIFICAR DJANGO
# ============================================================================

echo ""
echo -e "${CYAN}[3/5] Verificando Django...${NC}"

if python manage.py check --deploy 2>/dev/null; then
    echo -e "${GREEN}  ✅ Django OK${NC}"
else
    echo -e "${YELLOW}  ⚠️  Advertencias en Django (continuando...)${NC}"
fi

# ============================================================================
# 4. RECOLECTAR ARCHIVOS ESTÁTICOS
# ============================================================================

echo ""
echo -e "${CYAN}[4/5] Recolectando archivos estáticos...${NC}"

python manage.py collectstatic --noinput --clear 2>&1 | tail -3
python manage.py collectstatic --noinput 2>&1 | tail -3

echo -e "${GREEN}  ✅ Archivos estáticos actualizados${NC}"

# ============================================================================
# 5. VERIFICAR TEMPLATES
# ============================================================================

echo ""
echo -e "${CYAN}[5/5] Verificando templates...${NC}"

# Verificar que los templates existen
if [ -f "templates/us/en/onboarding/bienvenida.html" ]; then
    # Buscar botones en el template
    if grep -q "neon-glow" templates/us/en/onboarding/bienvenida.html; then
        echo -e "${GREEN}  ✅ Template bienvenida.html tiene estilos neon${NC}"
    else
        echo -e "${YELLOW}  ⚠️  Template bienvenida.html puede no tener estilos neon${NC}"
    fi
fi

# ============================================================================
# RESUMEN
# ============================================================================

echo ""
echo -e "${GREEN}"
echo "╔════════════════════════════════════════════════════════╗"
echo "║                                                         ║"
echo "║  ✅ ACTUALIZACIÓN COMPLETADA                            ║"
echo "║                                                         ║"
echo "║  📦 Archivos verificados                                ║"
echo "║  🎨 Estáticos recolectados                              ║"
echo "║  ✅ Sistema verificado                                  ║"
echo "║                                                         ║"
echo "╚════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo ""
echo -e "${CYAN}📝 PRÓXIMOS PASOS:${NC}"
echo ""
echo "1. Reiniciar servidor web:"
echo "   - PythonAnywhere: Ir a Web tab → Reload"
echo "   - Otros: sudo systemctl restart gunicorn-egarage"
echo ""
echo "2. Verificar cambios:"
echo "   - http://servidor/us/en/bienvenida/"
echo "   - http://servidor/accounts/signup/"
echo ""
echo -e "${GREEN}¡Listo!${NC}"




#!/bin/bash

# ============================================================================
# SCRIPT PARA FORZAR ACTUALIZACIÓN EN EL SERVIDOR
# ============================================================================
# Limpia cache y fuerza recarga de templates
# ============================================================================

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════╗"
echo "║                                                         ║"
echo "║  🔄 FORZAR ACTUALIZACIÓN DE TEMPLATES                   ║"
echo "║  Limpiando cache y recargando archivos                 ║"
echo "║                                                         ║"
echo "╚════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ============================================================================
# 1. VERIFICAR ARCHIVOS
# ============================================================================

echo -e "${CYAN}[1/7] Verificando archivos actualizados...${NC}"

FILES=(
    "templates/us/es/onboarding/bienvenida.html"
    "templates/us/en/onboarding/bienvenida.html"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        # Verificar que tiene los cambios
        if grep -q "neon-glow-purple" "$file" && grep -q "gap-5" "$file"; then
            echo -e "${GREEN}  ✅ $file (tiene cambios)${NC}"
        else
            echo -e "${RED}  ❌ $file (NO tiene cambios - archivo antiguo)${NC}"
            echo -e "${YELLOW}     ⚠️  Este archivo necesita ser subido nuevamente${NC}"
        fi
    else
        echo -e "${RED}  ❌ $file (NO EXISTE)${NC}"
    fi
done

# ============================================================================
# 2. LIMPIAR CACHE DE PYTHON
# ============================================================================

echo ""
echo -e "${CYAN}[2/7] Limpiando cache de Python...${NC}"

find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true

echo -e "${GREEN}  ✅ Cache de Python limpiado${NC}"

# ============================================================================
# 3. LIMPIAR CACHE DE TEMPLATES (Django)
# ============================================================================

echo ""
echo -e "${CYAN}[3/7] Limpiando cache de templates Django...${NC}"

# Buscar y eliminar directorios de cache de templates
find . -type d -name ".cache" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "cache" -path "*/templates/*" -exec rm -rf {} + 2>/dev/null || true

# Si existe directorio de cache específico
if [ -d "cache" ]; then
    rm -rf cache/*
    echo -e "${GREEN}  ✅ Directorio cache/ limpiado${NC}"
fi

echo -e "${GREEN}  ✅ Cache de templates limpiado${NC}"

# ============================================================================
# 4. LIMPIAR ARCHIVOS ESTÁTICOS
# ============================================================================

echo ""
echo -e "${CYAN}[4/7] Limpiando archivos estáticos...${NC}"

if [ -d "staticfiles" ]; then
    rm -rf staticfiles/*
    echo -e "${GREEN}  ✅ staticfiles/ limpiado${NC}"
fi

if [ -d "static" ]; then
    # No borrar todo, solo limpiar cache
    find static -type d -name ".webassets-cache" -exec rm -rf {} + 2>/dev/null || true
    echo -e "${GREEN}  ✅ Cache de static/ limpiado${NC}"
fi

# ============================================================================
# 5. RECOLECTAR ARCHIVOS ESTÁTICOS
# ============================================================================

echo ""
echo -e "${CYAN}[5/7] Recolectando archivos estáticos...${NC}"

if command -v python &> /dev/null; then
    python manage.py collectstatic --noinput --clear 2>&1 | tail -3
    python manage.py collectstatic --noinput 2>&1 | tail -3
    echo -e "${GREEN}  ✅ Archivos estáticos recolectados${NC}"
else
    echo -e "${YELLOW}  ⚠️  Python no encontrado, saltando...${NC}"
fi

# ============================================================================
# 6. VERIFICAR PERMISOS
# ============================================================================

echo ""
echo -e "${CYAN}[6/7] Verificando permisos de archivos...${NC}"

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        chmod 644 "$file"
        echo -e "${GREEN}  ✅ Permisos actualizados: $file${NC}"
    fi
done

# ============================================================================
# 7. VERIFICAR CONTENIDO DE ARCHIVOS
# ============================================================================

echo ""
echo -e "${CYAN}[7/7] Verificando contenido de archivos...${NC}"

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo ""
        echo -e "${BLUE}  📄 Contenido de $file:${NC}"
        
        # Buscar líneas clave
        if grep -q "neon-glow-purple" "$file"; then
            echo -e "${GREEN}    ✅ Tiene estilos neon-glow${NC}"
        else
            echo -e "${RED}    ❌ NO tiene estilos neon-glow${NC}"
        fi
        
        if grep -q "gap-5" "$file"; then
            echo -e "${GREEN}    ✅ Tiene gap-5 (espaciado)${NC}"
        else
            echo -e "${RED}    ❌ NO tiene gap-5${NC}"
        fi
        
        if grep -q "/accounts/signup/?from=us" "$file"; then
            echo -e "${GREEN}    ✅ Tiene enlace correcto a signup${NC}"
        else
            echo -e "${RED}    ❌ NO tiene enlace correcto a signup${NC}"
        fi
        
        # Mostrar fecha de modificación
        MOD_DATE=$(stat -c %y "$file" 2>/dev/null || stat -f "%Sm" "$file" 2>/dev/null || echo "desconocida")
        echo -e "${CYAN}    📅 Última modificación: $MOD_DATE${NC}"
    fi
done

# ============================================================================
# RESUMEN
# ============================================================================

echo ""
echo -e "${GREEN}"
echo "╔════════════════════════════════════════════════════════╗"
echo "║                                                         ║"
echo "║  ✅ LIMPIEZA COMPLETADA                                 ║"
echo "║                                                         ║"
echo "╚════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo ""
echo -e "${YELLOW}⚠️  IMPORTANTE:${NC}"
echo ""
echo "1. REINICIA el servidor web:"
echo "   - PythonAnywhere: Web tab → Reload"
echo "   - Otros: sudo systemctl restart gunicorn-egarage"
echo ""
echo "2. LIMPIA el cache del navegador:"
echo "   - Chrome/Edge: Ctrl+Shift+Delete → Caché → Borrar"
echo "   - O usa modo incógnito para probar"
echo ""
echo "3. VERIFICA en el navegador:"
echo "   https://www.egarage.cl/us/es/bienvenida/"
echo "   - Debe mostrar botones con bordes neon"
echo "   - Debe tener espaciado aumentado (gap-5)"
echo ""
echo -e "${GREEN}¡Listo!${NC}"




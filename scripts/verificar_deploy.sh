#!/bin/bash
# Script de Verificación Post-Deploy
# Ejecutar en el servidor después del deploy

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Verificación Post-Deploy${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 1. Verificar que los archivos existen
echo -e "${YELLOW}1. Verificando archivos...${NC}"
FILES=(
    "taller/views_extra/signup_redirects.py"
    "taller/forms/custom_signup.py"
    "templates/account/signup.html"
    "taller/views_extra/custom_signup.py"
    "gestion_taller/urls.py"
    "gestion_taller/settings.py"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "  ${GREEN}✓${NC} $file"
    else
        echo -e "  ${RED}✗${NC} $file (FALTANTE)"
        exit 1
    fi
done

echo ""

# 2. Verificar sintaxis Python
echo -e "${YELLOW}2. Verificando sintaxis Python...${NC}"
python -m py_compile taller/views_extra/signup_redirects.py 2>&1 && echo -e "  ${GREEN}✓${NC} signup_redirects.py"
python -m py_compile taller/forms/custom_signup.py 2>&1 && echo -e "  ${GREEN}✓${NC} custom_signup.py"
python -m py_compile taller/views_extra/custom_signup.py 2>&1 && echo -e "  ${GREEN}✓${NC} custom_signup.py"
python -m py_compile gestion_taller/urls.py 2>&1 && echo -e "  ${GREEN}✓${NC} urls.py"

echo ""

# 3. Verificar Django check
echo -e "${YELLOW}3. Verificando Django check...${NC}"
python manage.py check --deploy && echo -e "  ${GREEN}✓${NC} Django check OK" || {
    echo -e "  ${RED}✗${NC} Django check falló"
    exit 1
}

echo ""

# 4. Verificar que ACCOUNT_USERNAME_REQUIRED está en settings
echo -e "${YELLOW}4. Verificando settings.py...${NC}"
if grep -q "ACCOUNT_USERNAME_REQUIRED = False" gestion_taller/settings.py; then
    echo -e "  ${GREEN}✓${NC} ACCOUNT_USERNAME_REQUIRED = False configurado"
else
    echo -e "  ${YELLOW}⚠${NC} ACCOUNT_USERNAME_REQUIRED = False no encontrado (verificar manualmente)"
fi

echo ""

# 5. Test de importación
echo -e "${YELLOW}5. Test de importación de módulos...${NC}"
python -c "from taller.views_extra.signup_redirects import signup_redirect" && echo -e "  ${GREEN}✓${NC} signup_redirects import OK"
python -c "from taller.forms.custom_signup import CustomSignupForm" && echo -e "  ${GREEN}✓${NC} CustomSignupForm import OK"
python -c "from taller.views_extra.custom_signup import CustomSignupView" && echo -e "  ${GREEN}✓${NC} CustomSignupView import OK"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ Verificación completada${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Próximos pasos:${NC}"
echo "  1. Reiniciar aplicación Django"
echo "  2. Test: curl -I http://localhost/accounts/signup/?from=cl"
echo "  3. Test: curl -I http://localhost/cl/accounts/signup/"
echo ""

#!/bin/bash
# Script de Deploy - Registro Simplificado
# Uso: ./scripts/deploy_signup_simplificado.sh [usuario@servidor] [ruta_en_servidor]

set -e  # Salir si hay error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Variables
SERVER="${1:-usuario@servidor.com}"
SERVER_PATH="${2:-/ruta/a/egarage}"
LOCAL_PATH="$(pwd)"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deploy: Registro Simplificado${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "manage.py" ]; then
    echo -e "${RED}ERROR: No se encontró manage.py. Ejecuta este script desde la raíz del proyecto.${NC}"
    exit 1
fi

echo -e "${YELLOW}Paso 1: Verificando archivos locales...${NC}"
FILES=(
    "taller/views_extra/signup_redirects.py"
    "taller/forms/custom_signup.py"
    "templates/account/signup.html"
    "taller/views_extra/custom_signup.py"
    "gestion_taller/urls.py"
    "gestion_taller/settings.py"
    "taller/urls_extra/brasil.py"
    "taller/urls_extra/colombia.py"
    "taller/urls_extra/ecuador.py"
    "taller/urls_extra/mexico.py"
    "taller/urls_extra/peru.py"
    "taller/urls_extra/venezuela.py"
)

MISSING_FILES=()
for file in "${FILES[@]}"; do
    if [ ! -f "$file" ]; then
        MISSING_FILES+=("$file")
    fi
done

if [ ${#MISSING_FILES[@]} -gt 0 ]; then
    echo -e "${RED}ERROR: Archivos faltantes:${NC}"
    for file in "${MISSING_FILES[@]}"; do
        echo -e "  ${RED}- $file${NC}"
    done
    exit 1
fi

echo -e "${GREEN}✓ Todos los archivos encontrados${NC}"
echo ""

echo -e "${YELLOW}Paso 2: Copiando archivos al servidor...${NC}"
for file in "${FILES[@]}"; do
    echo -n "  Copiando $file... "
    # Crear directorio en servidor si no existe
    dir=$(dirname "$file")
    ssh "$SERVER" "mkdir -p ${SERVER_PATH}/${dir}"
    # Copiar archivo
    scp "$file" "${SERVER}:${SERVER_PATH}/${file}"
    echo -e "${GREEN}✓${NC}"
done

echo ""
echo -e "${YELLOW}Paso 3: Configurando permisos en servidor...${NC}"
ssh "$SERVER" "chmod 644 ${SERVER_PATH}/taller/views_extra/signup_redirects.py"
ssh "$SERVER" "chmod 644 ${SERVER_PATH}/taller/forms/custom_signup.py"
ssh "$SERVER" "chmod 644 ${SERVER_PATH}/templates/account/signup.html"
ssh "$SERVER" "chmod 644 ${SERVER_PATH}/taller/views_extra/custom_signup.py"
ssh "$SERVER" "chmod 644 ${SERVER_PATH}/gestion_taller/urls.py"
ssh "$SERVER" "chmod 644 ${SERVER_PATH}/gestion_taller/settings.py"
ssh "$SERVER" "chmod 644 ${SERVER_PATH}/taller/urls_extra/*.py"
echo -e "${GREEN}✓ Permisos configurados${NC}"

echo ""
echo -e "${YELLOW}Paso 4: Verificando sintaxis Python en servidor...${NC}"
ssh "$SERVER" "cd ${SERVER_PATH} && python manage.py check --deploy" || {
    echo -e "${RED}ERROR: Verificación de Django falló${NC}"
    echo -e "${YELLOW}Verifica manualmente los errores en el servidor${NC}"
    exit 1
}
echo -e "${GREEN}✓ Sintaxis correcta${NC}"

echo ""
echo -e "${YELLOW}Paso 5: Reiniciando aplicación...${NC}"
# Intentar diferentes métodos de restart
if ssh "$SERVER" "systemctl is-active --quiet gunicorn" 2>/dev/null; then
    echo "  Reiniciando gunicorn..."
    ssh "$SERVER" "sudo systemctl restart gunicorn"
    echo -e "${GREEN}✓ Gunicorn reiniciado${NC}"
elif ssh "$SERVER" "systemctl is-active --quiet uwsgi" 2>/dev/null; then
    echo "  Reiniciando uwsgi..."
    ssh "$SERVER" "sudo systemctl restart uwsgi"
    echo -e "${GREEN}✓ uWSGI reiniciado${NC}"
elif ssh "$SERVER" "test -f /var/www/*_wsgi.py" 2>/dev/null; then
    echo "  Reiniciando PythonAnywhere..."
    ssh "$SERVER" "touch /var/www/*_wsgi.py"
    echo -e "${GREEN}✓ PythonAnywhere reiniciado (touch wsgi.py)${NC}"
else
    echo -e "${YELLOW}⚠ No se detectó método de restart automático${NC}"
    echo -e "${YELLOW}Reinicia manualmente la aplicación Django${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ Deploy completado${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Próximos pasos:${NC}"
echo "  1. Verificar registro: https://tudominio.com/accounts/signup/?from=cl"
echo "  2. Verificar redirect: https://tudominio.com/cl/accounts/signup/"
echo "  3. Test registro completo con teléfono"
echo ""

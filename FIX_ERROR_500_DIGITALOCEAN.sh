#!/bin/bash
# ============================================
# Script: Fix Error 500 en DigitalOcean
# Soluciona problemas comunes de ALLOWED_HOSTS y permisos de BD
# ============================================

set -e

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}🔧 Fix Error 500 - DigitalOcean${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# Detectar ruta del proyecto
if [ -d "/srv/egarage" ]; then
    PROJECT_DIR="/srv/egarage"
elif [ -d "/home/egarage/app" ]; then
    PROJECT_DIR="/home/egarage/app"
elif [ -d "/var/www/egarage" ]; then
    PROJECT_DIR="/var/www/egarage"
else
    echo -e "${YELLOW}⚠️  Buscando directorio del proyecto...${NC}"
    PROJECT_DIR=$(find /home /srv /var/www -name "manage.py" -type f 2>/dev/null | head -1 | xargs dirname)
    if [ -z "$PROJECT_DIR" ]; then
        echo -e "${RED}❌ No se encontró el directorio del proyecto${NC}"
        echo "Por favor, ejecuta: cd /ruta/a/tu/proyecto"
        exit 1
    fi
fi

echo -e "${YELLOW}📁 Directorio del proyecto: ${PROJECT_DIR}${NC}"
cd "$PROJECT_DIR"

SETTINGS_FILE="$PROJECT_DIR/gestion_taller/settings.py"

# ============================================
# Paso 1: Verificar y actualizar ALLOWED_HOSTS
# ============================================
echo ""
echo -e "${CYAN}▶ Paso 1: Verificando ALLOWED_HOSTS...${NC}"

if [ ! -f "$SETTINGS_FILE" ]; then
    echo -e "${RED}❌ No se encontró settings.py en: $SETTINGS_FILE${NC}"
    exit 1
fi

# Verificar si ya tiene los hosts correctos en el default
if grep -q "ALLOWED_HOSTS = env_list(\"DJANGO_ALLOWED_HOSTS\", \[\"159.223.200.106\", \"localhost\", \"egarage.cl\", \"www.egarage.cl\"" "$SETTINGS_FILE"; then
    echo -e "${GREEN}✅ ALLOWED_HOSTS ya está configurado correctamente en settings.py${NC}"
else
    echo -e "${YELLOW}⚠️  Actualizando ALLOWED_HOSTS en settings.py...${NC}"
    # Backup
    cp "$SETTINGS_FILE" "${SETTINGS_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
    
    # Actualizar la línea de ALLOWED_HOSTS
    sed -i 's/ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", \[.*\]/ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", ["159.223.200.106", "localhost", "egarage.cl", "www.egarage.cl", "garage.cl", "www.garage.cl"]/' "$SETTINGS_FILE"
    echo -e "${GREEN}✅ ALLOWED_HOSTS actualizado${NC}"
fi

# Verificar variable de entorno .env
ENV_FILE="$PROJECT_DIR/.env"
if [ -f "$ENV_FILE" ]; then
    if grep -q "DJANGO_ALLOWED_HOSTS" "$ENV_FILE"; then
        echo -e "${YELLOW}⚠️  Variable DJANGO_ALLOWED_HOSTS encontrada en .env${NC}"
        echo -e "${CYAN}   Verificando valor...${NC}"
        if ! grep -q "DJANGO_ALLOWED_HOSTS=.*159.223.200.106.*egarage.cl.*www.egarage.cl" "$ENV_FILE"; then
            echo -e "${YELLOW}   Actualizando .env...${NC}"
            sed -i 's/^DJANGO_ALLOWED_HOSTS=.*/DJANGO_ALLOWED_HOSTS=159.223.200.106,localhost,egarage.cl,www.egarage.cl/' "$ENV_FILE"
            echo -e "${GREEN}✅ .env actualizado${NC}"
        else
            echo -e "${GREEN}✅ .env ya tiene los hosts correctos${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Agregando DJANGO_ALLOWED_HOSTS a .env...${NC}"
        echo "" >> "$ENV_FILE"
        echo "# ALLOWED_HOSTS para DigitalOcean" >> "$ENV_FILE"
        echo "DJANGO_ALLOWED_HOSTS=159.223.200.106,localhost,egarage.cl,www.egarage.cl" >> "$ENV_FILE"
        echo -e "${GREEN}✅ Variable agregada a .env${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  No se encontró archivo .env (opcional)${NC}"
fi

# ============================================
# Paso 2: Ajustar permisos de la base de datos
# ============================================
echo ""
echo -e "${CYAN}▶ Paso 2: Ajustando permisos de la base de datos...${NC}"

# Buscar archivo db.sqlite3
DB_FILE=$(find "$PROJECT_DIR" -name "db.sqlite3" -type f 2>/dev/null | head -1)

if [ -n "$DB_FILE" ]; then
    echo -e "${YELLOW}📁 Base de datos encontrada: $DB_FILE${NC}"
    
    # Cambiar dueño a www-data
    echo -e "${CYAN}   Cambiando dueño a www-data...${NC}"
    sudo chown www-data:www-data "$DB_FILE" || chown www-data:www-data "$DB_FILE" 2>/dev/null || echo -e "${YELLOW}   ⚠️  No se pudo cambiar dueño (puede requerir sudo)${NC}"
    
    # Permisos del archivo
    chmod 664 "$DB_FILE" || sudo chmod 664 "$DB_FILE"
    echo -e "${GREEN}✅ Permisos del archivo ajustados (664)${NC}"
    
    # Permisos del directorio
    DB_DIR=$(dirname "$DB_FILE")
    chmod 775 "$DB_DIR" || sudo chmod 775 "$DB_DIR"
    echo -e "${GREEN}✅ Permisos del directorio ajustados (775)${NC}"
else
    echo -e "${YELLOW}⚠️  No se encontró db.sqlite3 (puede estar usando PostgreSQL)${NC}"
fi

# Cambiar dueño de todo el proyecto (por si acaso)
echo ""
echo -e "${CYAN}   Cambiando dueño de todo el proyecto a www-data...${NC}"
sudo chown -R www-data:www-data "$PROJECT_DIR" || echo -e "${YELLOW}   ⚠️  No se pudo cambiar dueño completo (puede requerir sudo)${NC}"
echo -e "${GREEN}✅ Permisos del proyecto ajustados${NC}"

# ============================================
# Paso 3: Reiniciar servicios
# ============================================
echo ""
echo -e "${CYAN}▶ Paso 3: Reiniciando servicios...${NC}"

# Reiniciar gunicorn
if systemctl is-active --quiet gunicorn 2>/dev/null; then
    echo -e "${CYAN}   Reiniciando gunicorn...${NC}"
    sudo systemctl restart gunicorn
    echo -e "${GREEN}✅ Gunicorn reiniciado${NC}"
elif systemctl is-active --quiet egarage 2>/dev/null; then
    echo -e "${CYAN}   Reiniciando egarage...${NC}"
    sudo systemctl restart egarage
    echo -e "${GREEN}✅ Servicio egarage reiniciado${NC}"
elif systemctl is-active --quiet django 2>/dev/null; then
    echo -e "${CYAN}   Reiniciando django...${NC}"
    sudo systemctl restart django
    echo -e "${GREEN}✅ Servicio django reiniciado${NC}"
else
    echo -e "${YELLOW}⚠️  No se encontró servicio systemd activo${NC}"
    echo -e "${YELLOW}   Verifica manualmente con: systemctl list-units --type=service | grep -E 'gunicorn|egarage|django'${NC}"
fi

# Reiniciar nginx
if systemctl is-active --quiet nginx 2>/dev/null; then
    echo -e "${CYAN}   Recargando nginx...${NC}"
    sudo systemctl reload nginx || sudo systemctl restart nginx
    echo -e "${GREEN}✅ Nginx recargado${NC}"
fi

# ============================================
# Resumen y comandos útiles
# ============================================
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Fix completado!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${CYAN}📋 Próximos pasos:${NC}"
echo ""
echo -e "${YELLOW}1. Ver logs en tiempo real:${NC}"
echo -e "   ${CYAN}sudo journalctl -u gunicorn -f${NC}"
echo -e "   ${CYAN}sudo journalctl -u egarage -f${NC}"
echo ""
echo -e "${YELLOW}2. Probar el sitio:${NC}"
echo -e "   ${CYAN}curl -I http://egarage.cl${NC}"
echo -e "   ${CYAN}curl -I http://www.egarage.cl${NC}"
echo ""
echo -e "${YELLOW}3. Ver logs de nginx si hay problemas:${NC}"
echo -e "   ${CYAN}sudo tail -f /var/log/nginx/error.log${NC}"
echo ""
echo -e "${YELLOW}4. Verificar estado de servicios:${NC}"
echo -e "   ${CYAN}sudo systemctl status gunicorn${NC}"
echo -e "   ${CYAN}sudo systemctl status nginx${NC}"
echo ""
echo -e "${YELLOW}5. Si el error persiste, revisa los logs:${NC}"
echo -e "   ${CYAN}sudo journalctl -u gunicorn --since '5 minutes ago'${NC}"
echo ""

#!/bin/bash

# ============================================
# Script: Commit, Push y Pull en Servidor
# eGarage - Diciembre 2024
# ============================================

set -e  # Salir si hay error

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}🚀 Commit, Push y Pull - eGarage${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# ============================================
# PARTE 1: COMMIT Y PUSH (LOCAL)
# ============================================

echo -e "${YELLOW}📦 Paso 1: Verificando estado de Git...${NC}"
git status --short

echo ""
read -p "¿Deseas continuar con commit y push? (s/n): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    echo -e "${RED}❌ Operación cancelada${NC}"
    exit 1
fi

# Verificar si hay cambios
if [ -z "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}⚠️  No hay cambios para commitear${NC}"
else
    echo -e "${YELLOW}📝 Agregando archivos modificados...${NC}"
    git add -u
    
    echo ""
    read -p "¿Agregar también archivos nuevos? (s/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        git add .
    fi
    
    echo ""
    read -p "Mensaje del commit: " commit_message
    
    if [ -z "$commit_message" ]; then
        commit_message="Actualización: $(date '+%Y-%m-%d %H:%M:%S')"
    fi
    
    echo -e "${YELLOW}💾 Haciendo commit...${NC}"
    git commit -m "$commit_message"
fi

# Verificar si hay commits sin push
if [ -n "$(git log origin/main..HEAD 2>/dev/null)" ]; then
    echo -e "${YELLOW}📤 Haciendo push...${NC}"
    git push origin main
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Push exitoso${NC}"
    else
        echo -e "${RED}❌ Error en push${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}ℹ️  No hay commits nuevos para pushear${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Commit y Push completados${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# ============================================
# PARTE 2: INSTRUCCIONES PARA EL SERVIDOR
# ============================================

echo -e "${YELLOW}📋 Instrucciones para actualizar el servidor:${NC}"
echo ""
echo "1. Conectarse al servidor:"
echo -e "   ${GREEN}ssh atlantareciclajes@ssh.pythonanywhere.com${NC}"
echo ""
echo "2. Ejecutar estos comandos en el servidor:"
echo ""
echo -e "${GREEN}cd ~/egarage && \\${NC}"
echo -e "${GREEN}git pull origin main && \\${NC}"
echo -e "${GREEN}pip3.10 install --user -r requirements.txt && \\${NC}"
echo -e "${GREEN}python3.10 manage.py migrate && \\${NC}"
echo -e "${GREEN}python3.10 manage.py collectstatic --noinput && \\${NC}"
echo -e "${GREEN}touch /var/www/atlantareciclajes_pythonanywhere_com_wsgi.py${NC}"
echo ""
echo "3. Verificar que funciona:"
echo -e "   ${GREEN}curl -I https://www.egarage.cl/${NC}"
echo ""

# Guardar comandos en archivo
SERVER_SCRIPT="actualizar_servidor_$(date +%Y%m%d_%H%M%S).sh"
cat > "$SERVER_SCRIPT" << 'EOF'
#!/bin/bash
# Script para ejecutar en el servidor
# Generado automáticamente

set -e

echo "🚀 Actualizando servidor eGarage..."

# Ir al directorio del proyecto
cd ~/egarage || cd /home/atlantareciclajes/apps/egarage/current

# Pull
echo "📥 Haciendo pull..."
git pull origin main

# Dependencias
echo "📦 Instalando dependencias..."
pip3.10 install --user -r requirements.txt

# Migraciones
echo "🗄️  Ejecutando migraciones..."
python3.10 manage.py migrate

# Estáticos
echo "📁 Recopilando archivos estáticos..."
python3.10 manage.py collectstatic --noinput

# Reiniciar
echo "🔄 Reiniciando aplicación..."
touch /var/www/atlantareciclajes_pythonanywhere_com_wsgi.py

echo "✅ Actualización completada!"
echo ""
echo "Verificar:"
echo "curl -I https://www.egarage.cl/"
EOF

chmod +x "$SERVER_SCRIPT"
echo -e "${GREEN}📄 Script guardado en: ${SERVER_SCRIPT}${NC}"
echo -e "${YELLOW}💡 Puedes copiar este archivo al servidor y ejecutarlo${NC}"
echo ""


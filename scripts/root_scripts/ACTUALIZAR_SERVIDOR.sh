#!/bin/bash
# Script completo para actualizar el servidor eGarage
# Uso: ./ACTUALIZAR_SERVIDOR.sh

set -e  # Salir si hay errores

echo "=" | cat
echo "🚀 ACTUALIZACIÓN DEL SERVIDOR eGARAGE" | cat
echo "=" | cat
echo "" | cat

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuración del servidor
SERVIDOR_USER="atlantareciclajes"
SERVIDOR_HOST="atlantareciclajes.pythonanywhere.com"
PROJECT_DIR="/home/atlantareciclajes/apps/egarage/current"
VENV_PATH="/home/atlantareciclajes/.virtualenvs/venv_egarage310"

echo -e "${YELLOW}📋 Información del servidor:${NC}"
echo "   Usuario: $SERVIDOR_USER"
echo "   Host: $SERVIDOR_HOST"
echo "   Directorio: $PROJECT_DIR"
echo "   Virtualenv: $VENV_PATH"
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "manage.py" ]; then
    echo -e "${RED}❌ Error: No se encontró manage.py${NC}"
    echo "   Ejecuta este script desde la raíz del proyecto"
    exit 1
fi

# Paso 1: Verificar cambios locales
echo -e "${GREEN}📝 Paso 1: Verificando cambios locales...${NC}"
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}⚠️  Hay cambios sin commit:${NC}"
    git status --short
    echo ""
    read -p "¿Deseas hacer commit de estos cambios? (s/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        git add .
        read -p "Mensaje del commit: " commit_message
        if [ -z "$commit_message" ]; then
            commit_message="chore: actualizar servidor - $(date +%Y-%m-%d)"
        fi
        git commit -m "$commit_message"
        echo -e "${GREEN}✅ Cambios commiteados${NC}"
    else
        echo -e "${YELLOW}⚠️  Saltando commit${NC}"
    fi
else
    echo -e "${GREEN}✅ No hay cambios pendientes${NC}"
fi

# Paso 2: Push a GitHub
echo ""
echo -e "${GREEN}📤 Paso 2: Pusheando a GitHub...${NC}"
current_branch=$(git branch --show-current)
echo "   Rama actual: $current_branch"
read -p "¿Deseas hacer push a GitHub? (s/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Ss]$ ]]; then
    git push origin $current_branch
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Push exitoso${NC}"
    else
        echo -e "${RED}❌ Error en el push${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  Saltando push${NC}"
fi

# Paso 3: Instrucciones para el servidor
echo ""
echo -e "${GREEN}📋 Paso 3: Instrucciones para actualizar en el servidor${NC}"
echo ""
echo "Conectarse al servidor y ejecutar:"
echo ""
echo -e "${YELLOW}# Conectar al servidor${NC}"
echo "ssh $SERVIDOR_USER@ssh.pythonanywhere.com"
echo ""
echo -e "${YELLOW}# Ir al directorio del proyecto${NC}"
echo "cd $PROJECT_DIR"
echo ""
echo -e "${YELLOW}# Activar virtualenv${NC}"
echo "source $VENV_PATH/bin/activate"
echo ""
echo -e "${YELLOW}# Actualizar código desde Git${NC}"
echo "git pull origin main"
echo ""
echo -e "${YELLOW}# Instalar nuevas dependencias (si las hay)${NC}"
echo "pip install -r requirements.txt"
echo ""
echo -e "${YELLOW}# Ejecutar migraciones${NC}"
echo "python manage.py migrate"
echo ""
echo -e "${YELLOW}# Recopilar archivos estáticos${NC}"
echo "python manage.py collectstatic --noinput"
echo ""
echo -e "${YELLOW}# Ejecutar comando para arreglar testuser_usa${NC}"
echo "python manage.py fix_testuser_usa"
echo ""
echo -e "${YELLOW}# Reiniciar aplicación web${NC}"
echo "touch /var/www/${SERVIDOR_USER}_pythonanywhere_com_wsgi.py"
echo ""
echo -e "${YELLOW}# Verificar logs${NC}"
echo "tail -f ~/logs/user/error.log"
echo ""

# Paso 4: Generar script para ejecutar en servidor
echo -e "${GREEN}📝 Paso 4: Generando script para el servidor...${NC}"
cat > actualizar_en_servidor.sh << 'EOFSERVER'
#!/bin/bash
# Script para ejecutar EN EL SERVIDOR
# Uso: bash actualizar_en_servidor.sh

set -e

echo "=" | cat
echo "🔄 Actualizando servidor eGarage..." | cat
echo "=" | cat
echo "" | cat

# Variables
PROJECT_DIR="/home/atlantareciclajes/apps/egarage/current"
VENV_PATH="/home/atlantareciclajes/.virtualenvs/venv_egarage310"

# Ir al directorio del proyecto
cd "$PROJECT_DIR" || exit 1

# Activar virtualenv
echo "🔧 Activando virtualenv..."
source "$VENV_PATH/bin/activate"

# Actualizar código
echo ""
echo "📥 Actualizando código desde Git..."
git pull origin main

# Instalar dependencias
echo ""
echo "📦 Instalando dependencias..."
pip install -r requirements.txt --quiet

# Ejecutar migraciones
echo ""
echo "🗄️  Ejecutando migraciones..."
python manage.py migrate --noinput

# Recopilar estáticos
echo ""
echo "📁 Recopilando archivos estáticos..."
python manage.py collectstatic --noinput

# Arreglar testuser_usa si existe el comando
echo ""
echo "🔧 Verificando usuario testuser_usa..."
if python manage.py fix_testuser_usa 2>/dev/null; then
    echo "✅ Usuario testuser_usa actualizado"
else
    echo "⚠️  Comando fix_testuser_usa no disponible (continuando...)"
fi

# Reiniciar aplicación
echo ""
echo "🔄 Reiniciando aplicación web..."
touch /var/www/atlantareciclajes_pythonanywhere_com_wsgi.py

echo ""
echo "✅ Actualización completada!"
echo ""
echo "📋 Verificar logs:"
echo "   tail -f ~/logs/user/error.log"
echo ""
echo "🌐 Verificar sitio:"
echo "   https://www.egarage.cl/"
echo ""
EOFSERVER

chmod +x actualizar_en_servidor.sh
echo -e "${GREEN}✅ Script generado: actualizar_en_servidor.sh${NC}"
echo ""
echo "Puedes copiar este archivo al servidor y ejecutarlo:"
echo ""
echo "   scp actualizar_en_servidor.sh $SERVIDOR_USER@ssh.pythonanywhere.com:~/"
echo "   ssh $SERVIDOR_USER@ssh.pythonanywhere.com"
echo "   bash ~/actualizar_en_servidor.sh"
echo ""

# Paso 5: Generar comandos para copiar archivos específicos
echo -e "${GREEN}📝 Paso 5: Generando comandos para archivos específicos...${NC}"
cat > COMANDOS_COPIAR_ARCHIVOS.txt << 'EOFFILES'
# Comandos para copiar archivos específicos al servidor

# 1. Copiar archivos de gestión de usuarios
scp taller/management/commands/fix_testuser_usa.py \
    atlantareciclajes@ssh.pythonanywhere.com:/home/atlantareciclajes/apps/egarage/current/taller/management/commands/

# 2. Copiar archivos de multi-tenant hardening
scp taller/managers/empresa_aware.py \
    atlantareciclajes@ssh.pythonanywhere.com:/home/atlantareciclajes/apps/egarage/current/taller/managers/

scp taller/mixins/empresa_required.py \
    atlantareciclajes@ssh.pythonanywhere.com:/home/atlantareciclajes/apps/egarage/current/taller/mixins/

scp taller/middleware/tenant_isolation.py \
    atlantareciclajes@ssh.pythonanywhere.com:/home/atlantareciclajes/apps/egarage/current/taller/middleware/

scp taller/utils/tenant_audit.py \
    atlantareciclajes@ssh.pythonanywhere.com:/home/atlantareciclajes/apps/egarage/current/taller/utils/

# 3. Copiar archivos de formularios y vistas actualizados
scp taller/vehiculos/forms.py \
    atlantareciclajes@ssh.pythonanywhere.com:/home/atlantareciclajes/apps/egarage/current/taller/vehiculos/

scp taller/vehiculos/views_fbv.py \
    atlantareciclajes@ssh.pythonanywhere.com:/home/atlantareciclajes/apps/egarage/current/taller/vehiculos/

# 4. Copiar templates actualizados
scp templates/taller/us/en/vehiculos/crear_vehiculo.html \
    atlantareciclajes@ssh.pythonanywhere.com:/home/atlantareciclajes/apps/egarage/current/templates/taller/us/en/vehiculos/

# 5. Ejecutar en el servidor después de copiar
ssh atlantareciclajes@ssh.pythonanywhere.com << 'ENDSSH'
cd /home/atlantareciclajes/apps/egarage/current
source ~/.virtualenvs/venv_egarage310/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py fix_testuser_usa
touch /var/www/atlantareciclajes_pythonanywhere_com_wsgi.py
ENDSSH
EOFFILES

echo -e "${GREEN}✅ Comandos generados: COMANDOS_COPIAR_ARCHIVOS.txt${NC}"

# Resumen final
echo ""
echo "=" | cat
echo -e "${GREEN}✅ PROCESO COMPLETADO${NC}"
echo "=" | cat
echo ""
echo "📋 Archivos generados:"
echo "   1. actualizar_en_servidor.sh - Script para ejecutar en el servidor"
echo "   2. COMANDOS_COPIAR_ARCHIVOS.txt - Comandos para copiar archivos específicos"
echo ""
echo "🚀 Próximos pasos:"
echo "   1. Subir cambios a GitHub (si aún no lo hiciste)"
echo "   2. Conectarte al servidor: ssh $SERVIDOR_USER@ssh.pythonanywhere.com"
echo "   3. Ejecutar: bash actualizar_en_servidor.sh"
echo "   O seguir las instrucciones manuales mostradas arriba"
echo ""
echo "📚 Cambios incluidos en esta actualización:"
echo "   ✅ Fix testuser_usa (comando Django)"
echo "   ✅ Multi-tenant hardening (managers, mixins, middleware)"
echo "   ✅ Fix formulario de vehículos (marcas para USA)"
echo "   ✅ Documentación Alpine.js + HTMX"
echo ""


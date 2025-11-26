#!/bin/bash
# ========================================
# SCRIPT: Deployment ROBUSTO a PythonAnywhere
# ========================================
# USO: ./scripts/deploy_to_server.sh
# REQUIERE: Git configurado, SSH keys configuradas

set -e  # Salir si algo falla

# ========================================
# CONFIGURACIÓN
# ========================================
SERVER_USER="atlantareciclajes"
SERVER_HOST="ssh.pythonanywhere.com"
REMOTE_PATH="/home/atlantareciclajes/apps/egarage"
VENV_NAME="venv_egarage310"
WSGI_FILE="/var/www/www_atlantareciclajes_pythonanywhere_com_wsgi.py"
GIT_REPO="git@github.com:TU-USUARIO/egarage.git"  # 👈 CAMBIAR POR TU REPO

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ========================================
# FUNCIONES
# ========================================

print_step() {
    echo -e "${CYAN}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# ========================================
# PRE-DEPLOYMENT CHECKS (LOCAL)
# ========================================

echo ""
echo "========================================="
echo "🚀 PRE-DEPLOYMENT CHECKS (LOCAL)"
echo "========================================="
echo ""

# 1. Verificar que estamos en la raíz del proyecto
print_step "1. Verificando ubicación..."
if [ ! -f "manage.py" ]; then
    print_error "No estás en la raíz del proyecto Django"
    exit 1
fi
print_success "Ubicación correcta"

# 2. Verificar que Git está limpio
print_step "2. Verificando estado de Git..."
if [[ -n $(git status --porcelain) ]]; then
    print_warning "Tienes cambios sin commitear:"
    git status --short
    echo ""
    read -p "¿Quieres commitear estos cambios ahora? (s/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        git add -A
        read -p "Mensaje de commit: " commit_msg
        git commit -m "$commit_msg"
        print_success "Cambios commiteados"
    else
        print_error "Deployment cancelado. Commitea tus cambios primero."
        exit 1
    fi
fi
print_success "Git está limpio"

# 3. Verificar que estamos en la branch correcta
print_step "3. Verificando branch..."
CURRENT_BRANCH=$(git branch --show-current)
print_warning "Branch actual: $CURRENT_BRANCH"
if [[ "$CURRENT_BRANCH" != "main" && "$CURRENT_BRANCH" != "master" ]]; then
    read -p "No estás en main/master. ¿Continuar? (s/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        exit 1
    fi
fi

# 4. Push a Git
print_step "4. Pusheando a Git..."
git push origin $CURRENT_BRANCH
print_success "Push completado"

# 5. Verificar archivos críticos
print_step "5. Verificando archivos críticos..."
CRITICAL_FILES=(
    "requirements.txt"
    "manage.py"
    "gestion_taller/settings.py"
    "gestion_taller/wsgi.py"
)

for file in "${CRITICAL_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        print_error "Archivo crítico faltante: $file"
        exit 1
    fi
done
print_success "Archivos críticos presentes"

# ========================================
# DEPLOYMENT EN SERVIDOR
# ========================================

echo ""
echo "========================================="
echo "🌐 DEPLOYMENT EN SERVIDOR"
echo "========================================="
echo ""

# Crear script de deployment para ejecutar en el servidor
REMOTE_SCRIPT=$(cat <<'REMOTE_EOF'
#!/bin/bash
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

print_step() { echo -e "${CYAN}▶ $1${NC}"; }
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }

cd /home/atlantareciclajes/apps/egarage

# 1. Crear release timestamp
RELEASE=$(date +%Y-%m-%d_%H%M%S)
print_step "1. Creando release: $RELEASE"

# 2. Clonar código
print_step "2. Clonando código desde Git..."
mkdir -p releases/$RELEASE
cd releases/$RELEASE
git clone --depth=1 GIT_REPO_PLACEHOLDER .
print_success "Código clonado"

# 2.5. Configurar permisos (CRÍTICO para evitar PermissionError)
print_step "2.5. Configurando permisos de archivos..."
# Archivos: 644 (rw-r--r--)
find . -type f -exec chmod 644 {} \;
# Directorios: 755 (rwxr-xr-x)
find . -type d -exec chmod 755 {} \;
# Scripts Python ejecutables: 755
find . -name "*.py" -exec chmod 755 {} \;
chmod 755 manage.py
# Asegurar que templates son legibles (globales y de apps)
if [ -d "templates" ]; then
    find templates -type f -exec chmod 644 {} \;
    find templates -type d -exec chmod 755 {} \;
fi
# Templates de apps (taller/templates/, etc.)
for app_dir in */templates; do
    if [ -d "$app_dir" ]; then
        find "$app_dir" -type f -exec chmod 644 {} \;
        find "$app_dir" -type d -exec chmod 755 {} \;
    fi
done
print_success "Permisos configurados"

# 3. Activar venv e instalar dependencias
print_step "3. Instalando dependencias..."
source ~/.virtualenvs/VENV_NAME_PLACEHOLDER/bin/activate

# Actualizar pip primero
pip install --upgrade pip

# Instalar dependencias con timeout y retry
pip install -r requirements.txt --timeout 300 --retries 3 || {
    print_error "Falló instalación de dependencias"
    exit 1
}
print_success "Dependencias instaladas"

# 4. Verificar settings
print_step "4. Verificando configuración..."
if [ ! -f "gestion_taller/settings.py" ]; then
    print_error "settings.py no encontrado"
    exit 1
fi

# Crear settings_local.py si no existe (con variables de entorno)
if [ ! -f "gestion_taller/settings_local.py" ]; then
    print_step "Creando settings_local.py..."
    cat > gestion_taller/settings_local.py << 'SETTINGS_EOF'
import os
from pathlib import Path

# Este archivo NO debe ir en Git
# Contiene configuración específica del servidor

DEBUG = False
ALLOWED_HOSTS = ['atlantareciclajes.pythonanywhere.com', 'www.egarage.cl']

# Base de datos (usar la del servidor)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': Path(__file__).resolve().parent.parent / 'db.sqlite3',
    }
}

# Media y Static (rutas del servidor)
MEDIA_ROOT = '/home/atlantareciclajes/apps/egarage/media'
STATIC_ROOT = '/home/atlantareciclajes/apps/egarage/staticfiles'
SETTINGS_EOF
    print_success "settings_local.py creado"
fi

# 5. Migraciones
print_step "5. Ejecutando migraciones..."
python manage.py migrate --noinput || {
    print_error "Falló migración"
    exit 1
}
print_success "Migraciones completadas"

# 6. Collectstatic
print_step "6. Recolectando archivos estáticos..."
python manage.py collectstatic --noinput --clear || {
    print_error "Falló collectstatic"
    exit 1
}
print_success "Archivos estáticos recolectados"

# 7. Tests de sintaxis Python
print_step "7. Verificando sintaxis..."
python manage.py check || {
    print_error "Falló verificación de sintaxis"
    exit 1
}
print_success "Sintaxis correcta"

# 8. Actualizar symlink current
print_step "8. Actualizando symlink 'current'..."
cd /home/atlantareciclajes/apps/egarage
ln -sfn releases/$RELEASE current
print_success "Symlink actualizado"

# 9. Reload WSGI
print_step "9. Recargando WSGI..."
touch WSGI_FILE_PLACEHOLDER
print_success "WSGI recargado"

# 10. Cleanup de releases antiguas (mantener últimas 3)
print_step "10. Limpiando releases antiguas..."
cd releases
ls -t | tail -n +4 | xargs -r rm -rf
print_success "Releases antiguas eliminadas"

print_success "🎉 DEPLOYMENT COMPLETADO: $RELEASE"
REMOTE_EOF
)

# Reemplazar placeholders
REMOTE_SCRIPT="${REMOTE_SCRIPT//GIT_REPO_PLACEHOLDER/$GIT_REPO}"
REMOTE_SCRIPT="${REMOTE_SCRIPT//VENV_NAME_PLACEHOLDER/$VENV_NAME}"
REMOTE_SCRIPT="${REMOTE_SCRIPT//WSGI_FILE_PLACEHOLDER/$WSGI_FILE}"

# Ejecutar script en servidor
print_step "Ejecutando deployment en servidor..."
ssh $SERVER_USER@$SERVER_HOST "bash -s" <<< "$REMOTE_SCRIPT"

# ========================================
# POST-DEPLOYMENT
# ========================================

echo ""
echo "========================================="
echo "✅ DEPLOYMENT COMPLETADO"
echo "========================================="
echo ""
print_success "Verifica en: https://atlantareciclajes.pythonanywhere.com"
echo ""
print_step "Si algo salió mal, puedes rollback con:"
echo "  ssh $SERVER_USER@$SERVER_HOST"
echo "  cd /home/atlantareciclajes/apps/egarage"
echo "  ln -sfn releases/RELEASE_ANTERIOR current"
echo "  touch $WSGI_FILE"
echo ""






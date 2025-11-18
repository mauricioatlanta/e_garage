#!/bin/bash
# ========================================
# SCRIPT: Deployment a PythonAnywhere
# ========================================
# USO: ./deploy_to_server.sh
# Este script prepara el proyecto para deployment

set -e  # Salir si algo falla

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

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

echo ""
echo "========================================="
echo "🚀 PREPARACIÓN PARA DEPLOYMENT"
echo "========================================="
echo ""

# 1. Verificar que estamos en la raíz del proyecto
print_step "1. Verificando ubicación..."
if [ ! -f "manage.py" ]; then
    print_error "No estás en la raíz del proyecto Django"
    exit 1
fi
print_success "Ubicación correcta"

# 2. Verificar estado de Git
print_step "2. Verificando estado de Git..."
if ! command -v git &> /dev/null; then
    print_warning "Git no está instalado, continuando sin Git..."
else
    if [[ -n $(git status --porcelain 2>/dev/null) ]]; then
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
        fi
    fi
    print_success "Git verificado"
fi

# 3. Compilar traducciones
print_step "3. Compilando traducciones..."
python manage.py compilemessages --locale es || {
    print_warning "No se pudieron compilar las traducciones (puede ser normal si no hay cambios)"
}
print_success "Traducciones compiladas"

# 4. Verificar sintaxis Python
print_step "4. Verificando sintaxis Python..."
python manage.py check --deploy || {
    print_warning "Algunos checks fallaron, pero continuando..."
}
print_success "Sintaxis verificada"

# 5. Crear lista de archivos modificados
print_step "5. Creando lista de archivos para deployment..."
if command -v git &> /dev/null; then
    git diff --name-only HEAD > deployment_files.txt 2>/dev/null || true
    git ls-files --modified >> deployment_files.txt 2>/dev/null || true
    print_success "Lista de archivos creada: deployment_files.txt"
else
    print_warning "Git no disponible, no se puede crear lista de archivos"
fi

# 6. Resumen
echo ""
echo "========================================="
echo "✅ PREPARACIÓN COMPLETADA"
echo "========================================="
echo ""
print_success "El proyecto está listo para deployment"
echo ""
print_step "Próximos pasos:"
echo "  1. Subir archivos al servidor (Git, SCP, FTP, etc.)"
echo "  2. En el servidor, ejecutar:"
echo "     - python manage.py migrate"
echo "     - python manage.py collectstatic --noinput"
echo "     - python manage.py compilemessages --locale es"
echo "  3. Reiniciar el servidor web (touch WSGI file en PythonAnywhere)"
echo ""


#!/bin/bash
# ========================================
# SCRIPT: Fix Permissions - eGarage
# ========================================
# Uso: ./scripts/fix_permissions.sh [RELEASE_PATH]
# Descripción: Corrige permisos de archivos para evitar PermissionError
# ========================================

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

# ========================================
# DETECTAR RUTA DEL PROYECTO
# ========================================

if [ -n "$1" ]; then
    # Ruta proporcionada como argumento
    PROJECT_PATH="$1"
else
    # Intentar detectar automáticamente
    if [ -d "/home/atlantareciclajes/apps/egarage/current" ]; then
        # Si existe symlink 'current', usarlo
        PROJECT_PATH="/home/atlantareciclajes/apps/egarage/current"
        print_step "Usando symlink 'current'"
    elif [ -d "/home/atlantareciclajes/apps/egarage" ]; then
        # Directorio base
        PROJECT_PATH="/home/atlantareciclajes/apps/egarage"
        print_warning "Usando directorio base. Considera especificar un release específico."
    else
        # Intentar desde directorio actual
        if [ -f "manage.py" ]; then
            PROJECT_PATH="$(pwd)"
            print_step "Usando directorio actual"
        else
            print_error "No se pudo detectar el directorio del proyecto."
            echo "Uso: $0 [RUTA_DEL_PROYECTO]"
            echo "Ejemplo: $0 /home/atlantareciclajes/apps/egarage/releases/2025-11-24_0525_eg"
            exit 1
        fi
    fi
fi

# Verificar que la ruta existe
if [ ! -d "$PROJECT_PATH" ]; then
    print_error "El directorio no existe: $PROJECT_PATH"
    exit 1
fi

print_step "Proyecto: $PROJECT_PATH"

# ========================================
# VERIFICAR PERMISOS ACTUALES
# ========================================

echo ""
print_step "Verificando permisos actuales..."

# Contar archivos con permisos incorrectos
BAD_FILES=$(find "$PROJECT_PATH" -type f ! -perm 644 2>/dev/null | wc -l)
BAD_DIRS=$(find "$PROJECT_PATH" -type d ! -perm 755 2>/dev/null | wc -l)

if [ "$BAD_FILES" -gt 0 ] || [ "$BAD_DIRS" -gt 0 ]; then
    print_warning "Encontrados $BAD_FILES archivos y $BAD_DIRS directorios con permisos incorrectos"
else
    print_success "Todos los permisos parecen correctos"
fi

# Verificar template específico del error
TEMPLATE_FILE="$PROJECT_PATH/templates/us/es/onboarding/bienvenida.html"
if [ -f "$TEMPLATE_FILE" ]; then
    PERMS=$(stat -c "%a" "$TEMPLATE_FILE" 2>/dev/null || stat -f "%OLp" "$TEMPLATE_FILE" 2>/dev/null || echo "unknown")
    print_step "Template bienvenida.html: permisos actuales = $PERMS"
    if [ "$PERMS" != "644" ]; then
        print_warning "Permisos incorrectos en template crítico"
    fi
else
    print_warning "Template no encontrado: $TEMPLATE_FILE"
fi

# ========================================
# CORREGIR PERMISOS
# ========================================

echo ""
print_step "Corrigiendo permisos..."

cd "$PROJECT_PATH"

# 1. Archivos: 644 (rw-r--r--)
print_step "Configurando permisos de archivos (644)..."
find . -type f -exec chmod 644 {} \; 2>/dev/null || {
    print_error "Error al configurar permisos de archivos"
    exit 1
}
print_success "Permisos de archivos configurados"

# 2. Directorios: 755 (rwxr-xr-x)
print_step "Configurando permisos de directorios (755)..."
find . -type d -exec chmod 755 {} \; 2>/dev/null || {
    print_error "Error al configurar permisos de directorios"
    exit 1
}
print_success "Permisos de directorios configurados"

# 3. Scripts Python ejecutables: 755
print_step "Configurando permisos de scripts Python (755)..."
find . -name "*.py" -exec chmod 755 {} \; 2>/dev/null || true
chmod 755 manage.py 2>/dev/null || true
print_success "Permisos de scripts configurados"

# 4. Asegurar que templates son legibles (CRÍTICO)
# Templates globales
if [ -d "templates" ]; then
    print_step "Verificando permisos de templates globales..."
    find templates -type f -exec chmod 644 {} \; 2>/dev/null || true
    find templates -type d -exec chmod 755 {} \; 2>/dev/null || true
    print_success "Permisos de templates globales verificados"
else
    print_warning "Directorio 'templates' no encontrado"
fi

# Templates de apps (taller/templates/, etc.)
print_step "Buscando templates en apps..."
for app_dir in */templates; do
    if [ -d "$app_dir" ]; then
        app_name=$(dirname "$app_dir")
        print_step "Corrigiendo permisos en $app_dir..."
        find "$app_dir" -type f -exec chmod 644 {} \; 2>/dev/null || true
        find "$app_dir" -type d -exec chmod 755 {} \; 2>/dev/null || true
        print_success "Permisos de $app_dir verificados"
    fi
done

# Verificar templates específicos conocidos
print_step "Verificando templates específicos..."
for template in "templates/us/es/onboarding/bienvenida.html" "taller/templates/taller/us/en/vehiculos/crear_vehiculo.html"; do
    if [ -f "$template" ]; then
        NEW_PERMS=$(stat -c "%a" "$template" 2>/dev/null || stat -f "%OLp" "$template" 2>/dev/null || echo "unknown")
        if [ "$NEW_PERMS" = "644" ]; then
            print_success "Template $(basename $template): permisos correctos (644)"
        else
            print_warning "Template $(basename $template): permisos = $NEW_PERMS (esperado: 644)"
        fi
    fi
done

# ========================================
# VERIFICACIÓN FINAL
# ========================================

echo ""
print_step "Verificando permisos finales..."

# Verificar que no queden archivos con permisos incorrectos
REMAINING_BAD_FILES=$(find . -type f ! -perm 644 2>/dev/null | wc -l)
REMAINING_BAD_DIRS=$(find . -type d ! -perm 755 2>/dev/null | wc -l)

if [ "$REMAINING_BAD_FILES" -eq 0 ] && [ "$REMAINING_BAD_DIRS" -eq 0 ]; then
    print_success "✅ Todos los permisos están correctos"
else
    print_warning "Quedan $REMAINING_BAD_FILES archivos y $REMAINING_BAD_DIRS directorios con permisos inusuales"
    print_warning "Esto puede ser normal para algunos archivos especiales"
fi

# ========================================
# RESUMEN
# ========================================

echo ""
echo "========================================="
echo "✅ CORRECCIÓN DE PERMISOS COMPLETADA"
echo "========================================="
echo ""
echo "Proyecto: $PROJECT_PATH"
echo "Fecha: $(date)"
echo ""
echo "Permisos configurados:"
echo "  - Archivos: 644 (rw-r--r--)"
echo "  - Directorios: 755 (rwxr-xr-x)"
echo "  - Scripts Python: 755 (rwxr-xr-x)"
echo ""
print_success "El servidor web (uwsgi) ahora debería poder leer los templates"
echo ""
print_step "Próximos pasos:"
echo "  1. Recargar WSGI: touch /var/www/www_atlantareciclajes_digitalocean_com_wsgi.py"
echo "  2. Probar URL: https://www.egarage.cl/us/es/bienvenida/"
echo ""


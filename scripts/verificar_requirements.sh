#!/bin/bash
# Script para verificar si hay requirements faltantes en el servidor
# Compara requirements.txt con los paquetes instalados

set -e

echo "=========================================="
echo "🔍 Verificación de Requirements en el Servidor"
echo "=========================================="
echo ""

# 1. Buscar requirements.txt
REQUIREMENTS_FILE=""

# Buscar en ubicaciones comunes
if [ -f "requirements.txt" ]; then
    REQUIREMENTS_FILE="requirements.txt"
elif [ -f "../requirements.txt" ]; then
    REQUIREMENTS_FILE="../requirements.txt"
elif [ -f "$(dirname $0)/../requirements.txt" ]; then
    REQUIREMENTS_FILE="$(dirname $0)/../requirements.txt"
else
    echo "❌ No se encontró requirements.txt"
    echo ""
    echo "Ubicaciones buscadas:"
    echo "  - ./requirements.txt"
    echo "  - ../requirements.txt"
    echo "  - $(dirname $0)/../requirements.txt"
    echo ""
    echo "💡 Puedes especificar la ruta manualmente:"
    echo "   bash scripts/verificar_requirements.sh /ruta/a/requirements.txt"
    exit 1
fi

echo "📄 Archivo requirements.txt encontrado: $REQUIREMENTS_FILE"
echo ""

# 2. Verificar que pip está disponible
if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
    echo "❌ pip no está instalado o no está en PATH"
    exit 1
fi

PIP_CMD="pip"
if command -v pip3 &> /dev/null; then
    PIP_CMD="pip3"
fi

# 3. Verificar que Python está disponible
if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
    echo "❌ Python no está instalado o no está en PATH"
    exit 1
fi

PYTHON_CMD="python"
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
fi

echo "🐍 Python: $($PYTHON_CMD --version 2>&1)"
echo "📦 pip: $($PIP_CMD --version 2>&1)"
echo ""

# 4. Verificar si estamos en un entorno virtual
if [ -n "$VIRTUAL_ENV" ]; then
    echo "✅ Entorno virtual activo: $VIRTUAL_ENV"
else
    echo "⚠️  No hay entorno virtual activo (recomendado usar uno)"
fi
echo ""

# 5. Obtener lista de paquetes instalados
echo "🔍 Obteniendo paquetes instalados..."
INSTALLED_LIST=$(mktemp)
$PIP_CMD list --format=freeze > "$INSTALLED_LIST" 2>/dev/null || {
    echo "❌ Error al obtener lista de paquetes instalados"
    rm -f "$INSTALLED_LIST"
    exit 1
}

INSTALLED_COUNT=$(grep -c "^" "$INSTALLED_LIST" || echo "0")
echo "✅ $INSTALLED_COUNT paquetes instalados detectados"
echo ""

# 6. Parsear requirements.txt
echo "📦 Parseando requirements.txt..."
REQUIRED_LIST=$(mktemp)

# Extraer nombres de paquetes (ignorar comentarios y líneas vacías)
grep -v "^#" "$REQUIREMENTS_FILE" | grep -v "^$" | sed 's/#.*$//' | while IFS= read -r line; do
    # Extraer nombre del paquete (antes de ==, >=, <=, >, <, ~=, etc.)
    package=$(echo "$line" | sed -E 's/[[:space:]]*([^=<>~!]+).*/\1/' | tr '[:upper:]' '[:lower:]' | sed 's/[_-]/[-_]/g')
    if [ -n "$package" ]; then
        echo "$package|$line" >> "$REQUIRED_LIST"
    fi
done

REQUIRED_COUNT=$(wc -l < "$REQUIRED_LIST" 2>/dev/null || echo "0")
echo "✅ $REQUIRED_COUNT paquetes encontrados en requirements.txt"
echo ""

# 7. Comparar
echo "=========================================="
echo "📊 RESULTADO DE LA VERIFICACIÓN"
echo "=========================================="
echo ""

MISSING=0
OK=0

while IFS='|' read -r package line; do
    # Normalizar nombre (puede tener guiones o guiones bajos)
    normalized=$(echo "$package" | sed 's/[-_]/[-_]/g')
    
    # Buscar en instalados (buscar con guiones y guiones bajos)
    found=false
    installed_version=""
    
    while IFS='==' read -r inst_package inst_version; do
        inst_normalized=$(echo "$inst_package" | tr '[:upper:]' '[:lower:]' | sed 's/[-_]/[-_]/g')
        if echo "$inst_normalized" | grep -qE "^${normalized}$"; then
            found=true
            installed_version="$inst_version"
            break
        fi
    done < "$INSTALLED_LIST"
    
    if [ "$found" = true ]; then
        OK=$((OK + 1))
        if [ $OK -le 10 ]; then
            echo "✅ $package → $installed_version"
        fi
    else
        MISSING=$((MISSING + 1))
        echo "❌ $package (requerido: $line)"
    fi
done < "$REQUIRED_LIST"

if [ $OK -gt 10 ]; then
    echo "... y $((OK - 10)) más correctos"
fi

echo ""

# 8. Resumen
echo "=========================================="
echo "📊 RESUMEN"
echo "=========================================="
echo "✅ Correctos:        $OK"
echo "❌ Faltantes:        $MISSING"
echo ""

# 9. Recomendaciones
if [ $MISSING -gt 0 ]; then
    echo "❌ HAY PAQUETES FALTANTES"
    echo ""
    echo "💡 Para instalar los paquetes faltantes:"
    echo "   $PIP_CMD install -r $REQUIREMENTS_FILE"
    echo ""
    echo "💡 O si estás en un entorno virtual:"
    echo "   source venv/bin/activate  # o tu entorno virtual"
    echo "   $PIP_CMD install -r $REQUIREMENTS_FILE"
    echo ""
    
    # Limpiar archivos temporales
    rm -f "$INSTALLED_LIST" "$REQUIRED_LIST"
    exit 1
else
    echo "✅ TODOS LOS REQUIREMENTS ESTÁN INSTALADOS"
    echo ""
    
    # Verificar versiones (básico, requiere pip check)
    echo "🔍 Verificando conflictos de dependencias..."
    if $PIP_CMD check 2>&1 | grep -q "No broken requirements"; then
        echo "✅ No hay conflictos de dependencias"
    else
        echo "⚠️  Posibles conflictos detectados:"
        $PIP_CMD check 2>&1 | grep -v "No broken requirements" || true
    fi
    echo ""
fi

# Limpiar archivos temporales
rm -f "$INSTALLED_LIST" "$REQUIRED_LIST"

echo "=========================================="
echo "✅ Verificación completada"
echo "=========================================="

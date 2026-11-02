#!/bin/bash
# Script para verificar y corregir ia_urls.py en el servidor

PROJECT_PATH="/home/atlantareciclajes/apps/egarage/current"
IA_URLS="${PROJECT_PATH}/taller/ia_urls.py"
IA_VIEWS="${PROJECT_PATH}/taller/ia_views.py"

echo "======================================================"
echo "🔍 VERIFICACIÓN DE IA_URLS.PY"
echo "======================================================"
echo ""

# Verificar que existe ia_views.py
if [ ! -f "$IA_VIEWS" ]; then
    echo "❌ ERROR: No se encontró taller/ia_views.py"
    echo "   Ubicación esperada: $IA_VIEWS"
    echo ""
    echo "💡 SOLUCIÓN:"
    echo "   1. Asegúrate de que ia_views.py esté en el paquete de actualización"
    echo "   2. O comenta las líneas que usan ia_views en ia_urls.py"
    exit 1
else
    echo "✅ taller/ia_views.py existe"
fi

# Verificar que existe ia_urls.py
if [ ! -f "$IA_URLS" ]; then
    echo "❌ ERROR: No se encontró taller/ia_urls.py"
    echo "   Ubicación esperada: $IA_URLS"
    exit 1
else
    echo "✅ taller/ia_urls.py existe"
fi

# Verificar que tiene la importación
if grep -q "from . import ia_views" "$IA_URLS"; then
    echo "✅ Importación correcta: 'from . import ia_views'"
else
    echo "❌ ERROR: No se encontró la importación 'from . import ia_views'"
    echo ""
    echo "🔧 CORRIGIENDO..."
    
    # Crear backup
    cp "$IA_URLS" "${IA_URLS}.backup_$(date +%Y%m%d_%H%M%S)"
    
    # Agregar la importación después de la primera línea
    sed -i '/^from django.urls import path/a\\nfrom . import ia_views' "$IA_URLS"
    
    if grep -q "from . import ia_views" "$IA_URLS"; then
        echo "✅ Importación agregada correctamente"
    else
        echo "❌ ERROR: No se pudo agregar la importación automáticamente"
        echo ""
        echo "💡 CORRECCIÓN MANUAL:"
        echo "   Edita $IA_URLS y agrega después de la línea 1:"
        echo "   from . import ia_views"
        exit 1
    fi
fi

# Verificar sintaxis Python
echo ""
echo "🔍 Verificando sintaxis Python..."
cd "$PROJECT_PATH"
python3 -m py_compile "$IA_URLS" 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Sintaxis de ia_urls.py correcta"
else
    echo "❌ ERROR: Sintaxis incorrecta en ia_urls.py"
    exit 1
fi

python3 -m py_compile "$IA_VIEWS" 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Sintaxis de ia_views.py correcta"
else
    echo "❌ ERROR: Sintaxis incorrecta en ia_views.py"
    exit 1
fi

# Verificar que las funciones existen
echo ""
echo "🔍 Verificando funciones en ia_views.py..."
REQUIRED_FUNCTIONS=("sugerencias_basicas_demo" "obtener_sugerencias_vehiculo" "demo_sugerencias_vehiculo")
MISSING_FUNCTIONS=()

for func in "${REQUIRED_FUNCTIONS[@]}"; do
    if grep -q "def $func" "$IA_VIEWS"; then
        echo "✅ Función '$func' encontrada"
    else
        echo "❌ Función '$func' NO encontrada"
        MISSING_FUNCTIONS+=("$func")
    fi
done

if [ ${#MISSING_FUNCTIONS[@]} -gt 0 ]; then
    echo ""
    echo "❌ ERROR: Faltan funciones en ia_views.py:"
    printf '   - %s\n' "${MISSING_FUNCTIONS[@]}"
    exit 1
fi

echo ""
echo "======================================================"
echo "✅ VERIFICACIÓN COMPLETADA - TODO CORRECTO"
echo "======================================================"












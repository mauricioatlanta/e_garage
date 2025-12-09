#!/bin/bash
# Script para corregir ia_urls.py e ia_views.py en el servidor
# Copiar y pegar este script completo en la consola del servidor

PROJECT_PATH="/home/atlantareciclajes/apps/egarage/current"
IA_URLS="${PROJECT_PATH}/taller/ia_urls.py"
IA_VIEWS="${PROJECT_PATH}/taller/ia_views.py"

echo "======================================================"
echo "🔧 CORRECCIÓN DE IA_URLS.PY E IA_VIEWS.PY"
echo "======================================================"
echo ""

cd "$PROJECT_PATH"

# 1. Verificar si ia_views.py existe
if [ ! -f "$IA_VIEWS" ]; then
    echo "❌ ERROR: No se encontró taller/ia_views.py"
    echo "   Necesitas subir este archivo desde tu PC al servidor"
    echo ""
    echo "💡 SOLUCIÓN:"
    echo "   1. En tu PC, copia el archivo: taller/ia_views.py"
    echo "   2. Súbelo al servidor con FileZilla a:"
    echo "      /home/atlantareciclajes/apps/egarage/current/taller/ia_views.py"
    echo ""
    exit 1
else
    echo "✅ taller/ia_views.py existe"
fi

# 2. Verificar ia_urls.py
if [ ! -f "$IA_URLS" ]; then
    echo "❌ ERROR: No se encontró taller/ia_urls.py"
    exit 1
else
    echo "✅ taller/ia_urls.py existe"
fi

# 3. Verificar si la importación está comentada
if grep -q "^# from . import ia_views" "$IA_URLS"; then
    echo "⚠️  Importación está comentada, descomentando..."
    
    # Crear backup
    cp "$IA_URLS" "${IA_URLS}.backup_$(date +%Y%m%d_%H%M%S)"
    echo "   ✅ Backup creado"
    
    # Descomentar la línea
    sed -i 's/^# from . import ia_views/from . import ia_views/' "$IA_URLS"
    
    if grep -q "^from . import ia_views" "$IA_URLS"; then
        echo "   ✅ Importación descomentada correctamente"
    else
        echo "   ❌ ERROR: No se pudo descomentar automáticamente"
        echo ""
        echo "   💡 CORRECCIÓN MANUAL:"
        echo "      Edita $IA_URLS y cambia:"
        echo "      # from . import ia_views"
        echo "      por:"
        echo "      from . import ia_views"
        exit 1
    fi
elif grep -q "^from . import ia_views" "$IA_URLS"; then
    echo "✅ Importación ya está activa"
else
    echo "⚠️  No se encontró la importación, agregándola..."
    
    # Crear backup
    cp "$IA_URLS" "${IA_URLS}.backup_$(date +%Y%m%d_%H%M%S)"
    echo "   ✅ Backup creado"
    
    # Agregar después de la primera línea
    sed -i '/^from django.urls import path/a\\nfrom . import ia_views' "$IA_URLS"
    
    if grep -q "^from . import ia_views" "$IA_URLS"; then
        echo "   ✅ Importación agregada correctamente"
    else
        echo "   ❌ ERROR: No se pudo agregar automáticamente"
        echo ""
        echo "   💡 CORRECCIÓN MANUAL:"
        echo "      Edita $IA_URLS y agrega después de la línea 1:"
        echo "      from . import ia_views"
        exit 1
    fi
fi

# 4. Verificar sintaxis
echo ""
echo "🔍 Verificando sintaxis Python..."
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

# 5. Verificar funciones
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

# 6. Probar importación
echo ""
echo "🔍 Probando importación en Python..."
python3 << 'PYTHON_EOF'
try:
    import sys
    sys.path.insert(0, '/home/atlantareciclajes/apps/egarage/current')
    from taller import ia_views
    from taller import ia_urls
    print("✅ Importación exitosa")
    print(f"   - ia_views: {ia_views}")
    print(f"   - ia_urls: {ia_urls}")
except Exception as e:
    print(f"❌ ERROR en importación: {e}")
    sys.exit(1)
PYTHON_EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "======================================================"
    echo "✅ CORRECCIÓN COMPLETADA - TODO CORRECTO"
    echo "======================================================"
    echo ""
    echo "📝 Próximos pasos:"
    echo "   1. Recarga la aplicación en el panel de PythonAnywhere"
    echo "   2. Prueba acceder a las rutas de IA"
    echo ""
else
    echo ""
    echo "❌ ERROR: La importación falló"
    exit 1
fi










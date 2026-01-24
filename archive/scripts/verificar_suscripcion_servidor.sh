#!/bin/bash
# Script para verificar el contenido del archivo suscripcion.py en el servidor
# Ejecutar: bash verificar_suscripcion_servidor.sh

echo "=========================================="
echo "VERIFICACION DE suscripcion.py"
echo "=========================================="
echo ""

ARCHIVO="taller/views_extra/suscripcion.py"

# 1. Verificar que existe
if [ ! -f "$ARCHIVO" ]; then
    echo "❌ ERROR: El archivo no existe: $ARCHIVO"
    exit 1
fi

echo "✅ Archivo encontrado: $ARCHIVO"
echo ""

# 2. Mostrar líneas 62-68 (sección de validación)
echo "=========================================="
echo "LINEAS 62-68 (Sección de validación):"
echo "=========================================="
sed -n '62,68p' "$ARCHIVO"
echo ""

# 3. Buscar logging
echo "=========================================="
echo "BUSCANDO LOGGING:"
echo "=========================================="
echo "Buscando 'Formulario inválido' (con tilde):"
grep -n "Formulario inválido" "$ARCHIVO" || echo "  ❌ No encontrado"
echo ""

echo "Buscando 'Formulario invalido' (sin tilde):"
grep -n "Formulario invalido" "$ARCHIVO" || echo "  ❌ No encontrado"
echo ""

echo "Buscando 'logger.warning':"
grep -n "logger.warning" "$ARCHIVO" || echo "  ❌ No encontrado"
echo ""

echo "Buscando '[Registro]':"
grep -n "\[Registro\]" "$ARCHIVO" || echo "  ❌ No encontrado"
echo ""

# 4. Contar líneas totales
TOTAL=$(wc -l < "$ARCHIVO")
echo "=========================================="
echo "Total de líneas: $TOTAL"
echo "=========================================="

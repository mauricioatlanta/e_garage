#!/bin/bash
# Script para buscar problemas de JavaScript: getElementById().addEventListener sin verificación

echo "======================================================"
echo "BUSCANDO PROBLEMAS DE JAVASCRIPT..."
echo "======================================================"
echo ""

# Buscar en templates
echo "📁 Buscando en templates..."
grep -rn "getElementById.*\.addEventListener" templates/ --include="*.html" | head -20

echo ""
echo "======================================================"
echo "ARCHIVOS CON PROBLEMAS POTENCIALES:"
echo "======================================================"
echo ""

# Listar archivos con el patrón problemático
grep -rl "getElementById.*\.addEventListener" templates/ --include="*.html" | while read file; do
    echo "  - $file"
done

echo ""
echo "======================================================"
echo "PATRÓN A CORREGIR:"
echo "======================================================"
echo ""
echo "ANTES:"
echo "  document.getElementById('id').addEventListener('click', ...)"
echo ""
echo "DESPUÉS:"
echo "  const el = document.getElementById('id');"
echo "  if (el) {"
echo "    el.addEventListener('click', ...);"
echo "  }"
echo ""







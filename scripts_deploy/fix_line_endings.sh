#!/bin/bash
# ======================================================
# Script: FIX LINE ENDINGS (Windows to Unix)
# Convierte archivos .sh de CRLF a LF
# ======================================================

echo "======================================================"
echo "CONVIRTIENDO TERMINACIONES DE LINEA (CRLF -> LF)..."
echo "======================================================"
echo ""

cd /home/atlantareciclajes/scripts_deploy/

# Convertir cada archivo .sh
for file in *.sh; do
    if [ -f "$file" ]; then
        echo "Convirtiendo: $file"
        # Usar dos2unix si está disponible, o sed como alternativa
        if command -v dos2unix &> /dev/null; then
            dos2unix "$file"
        else
            # Alternativa con sed
            sed -i 's/\r$//' "$file"
        fi
        echo "   ✅ Convertido"
    fi
done

echo ""
echo "======================================================"
echo "✅ CONVERSION COMPLETADA"
echo "======================================================"
echo ""
echo "Ahora puedes ejecutar:"
echo "   ./2_actualizar_ESTRUCTURA_COMPLETA.sh"
echo ""










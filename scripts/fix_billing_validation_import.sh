#!/bin/bash
# Script para comentar la importación de billing_validation temporalmente
# Ejecutar en el servidor: sudo bash fix_billing_validation_import.sh

FILE="/srv/egarage/taller/documentos/views_export_sii.py"
BACKUP="${FILE}.backup_$(date +%Y%m%d_%H%M%S)"

echo "Comentando importación de billing_validation..."

# Hacer backup
cp "$FILE" "$BACKUP"
echo "✅ Backup creado: $BACKUP"

# Comentar la importación
sed -i 's/^from taller.utils.billing_validation import/# from taller.utils.billing_validation import/' "$FILE"

# Verificar
if grep -q "^# from taller.utils.billing_validation import" "$FILE"; then
    echo "✅ Importación comentada"
else
    echo "❌ Error: No se pudo comentar la importación"
    exit 1
fi

# Verificar si la función se usa en el archivo
if grep -q "validar_cliente_para_facturacion" "$FILE"; then
    echo "⚠️  ADVERTENCIA: La función validar_cliente_para_facturacion se usa en el archivo"
    echo "   Puede causar errores en tiempo de ejecución"
    echo "   Revisa el archivo para ver dónde se usa:"
    grep -n "validar_cliente_para_facturacion" "$FILE"
fi

echo ""
echo "Ahora reinicia el servicio:"
echo "  sudo systemctl restart egarage-gunicorn.service"

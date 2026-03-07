#!/bin/bash
# Script para comentar todas las importaciones de módulos faltantes
# Ejecutar en el servidor: sudo bash comentar_importaciones_faltantes.sh

INIT_FILE="/srv/egarage/taller/models/__init__.py"
BACKUP_FILE="${INIT_FILE}.backup_$(date +%Y%m%d_%H%M%S)"

echo "=========================================="
echo "🔧 COMENTANDO IMPORTACIONES PROBLEMÁTICAS"
echo "=========================================="
echo ""

# Hacer backup
cp "$INIT_FILE" "$BACKUP_FILE"
echo "✅ Backup creado: $BACKUP_FILE"
echo ""

# Lista de módulos que sabemos que faltan
MODULOS_FALTANTES=(
    "memoria_seguimiento"
    "regimen_fiscal"
)

echo "Comentando importaciones de módulos faltantes..."
for modulo in "${MODULOS_FALTANTES[@]}"; do
    echo "  - $modulo"
    # Comentar líneas que importan este módulo
    sed -i "s/^from \.$modulo import/# from .$modulo import/" "$INIT_FILE"
    sed -i "s/^from \.$modulo$/# from .$modulo/" "$INIT_FILE"
done

echo ""
echo "✅ Importaciones comentadas"
echo ""
echo "Verificando cambios:"
grep -n "memoria_seguimiento\|regimen_fiscal" "$INIT_FILE" | head -5
echo ""
echo "Ahora reinicia el servicio:"
echo "  sudo systemctl restart egarage-gunicorn.service"

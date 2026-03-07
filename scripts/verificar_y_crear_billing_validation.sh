#!/bin/bash
# Script para verificar y crear billing_validation si falta
# Ejecutar en el servidor: sudo bash verificar_y_crear_billing_validation.sh

UTILS_DIR="/srv/egarage/taller/utils"
FILE="$UTILS_DIR/billing_validation.py"

echo "Verificando billing_validation.py..."

if [ ! -f "$FILE" ]; then
    echo "❌ Archivo no existe, creando stub..."
    mkdir -p "$UTILS_DIR"
    
    cat > "$FILE" << 'PYTHON_EOF'
"""
Utilidades para validación de facturación - STUB TEMPORAL
"""
from typing import Dict, Any
from taller.models.clientes import Cliente

def validar_cliente_para_facturacion(cliente: Cliente) -> Dict[str, Any]:
    """Stub temporal."""
    try:
        is_ready = cliente.is_billing_ready() if hasattr(cliente, "is_billing_ready") else True
        missing = cliente.get_missing_billing_fields() if hasattr(cliente, "get_missing_billing_fields") else []
    except:
        is_ready = True
        missing = []
    return {
        "is_ready": is_ready,
        "missing_fields": missing,
        "can_export": is_ready,
        "message": f"Cliente listo" if is_ready else f"Campos faltantes: {missing}",
        "profile_status": {},
    }
PYTHON_EOF
    
    APP_USER=$(stat -c '%U' /srv/egarage)
    APP_GROUP=$(stat -c '%G' /srv/egarage)
    chown "$APP_USER:$APP_GROUP" "$FILE"
    chmod 644 "$FILE"
    echo "✅ Archivo creado"
else
    echo "✅ Archivo existe"
    ls -la "$FILE"
fi

echo ""
echo "Reiniciando servicio..."
systemctl restart egarage-gunicorn.service
sleep 3
systemctl status egarage-gunicorn.service --no-pager | head -15

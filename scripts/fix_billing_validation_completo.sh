#!/bin/bash
# Script para arreglar el problema de billing_validation
# Opción 1: Crear archivo stub temporal
# Opción 2: Comentar importación y llamadas

echo "=========================================="
echo "🔧 ARREGLANDO billing_validation"
echo "=========================================="
echo ""

# Crear directorio si no existe
mkdir -p /srv/egarage/taller/utils

# Crear archivo stub temporal
cat > /srv/egarage/taller/utils/billing_validation.py << 'PYTHON_EOF'
"""
Utilidades para validación de facturación - STUB TEMPORAL
Este es un archivo temporal hasta que se suba el archivo completo.
"""

from typing import Dict, Any
from taller.models.clientes import Cliente


def validar_cliente_para_facturacion(cliente: Cliente) -> Dict[str, Any]:
    """
    Stub temporal - devuelve que el cliente está listo.
    Reemplazar con el archivo completo cuando esté disponible.
    """
    try:
        # Intentar usar los métodos reales si existen
        is_ready = cliente.is_billing_ready() if hasattr(cliente, 'is_billing_ready') else True
        missing = cliente.get_missing_billing_fields() if hasattr(cliente, 'get_missing_billing_fields') else []
    except:
        is_ready = True
        missing = []
    
    return {
        "is_ready": is_ready,
        "missing_fields": missing,
        "can_export": is_ready,
        "message": f"El cliente '{cliente.nombre}' está listo para facturar." if is_ready else f"Campos faltantes: {', '.join(missing)}",
        "profile_status": {},
    }
PYTHON_EOF

# Ajustar permisos
APP_USER=$(stat -c '%U' /srv/egarage)
APP_GROUP=$(stat -c '%G' /srv/egarage)
chown "$APP_USER:$APP_GROUP" /srv/egarage/taller/utils/billing_validation.py
chmod 644 /srv/egarage/taller/utils/billing_validation.py

echo "✅ Archivo stub creado: /srv/egarage/taller/utils/billing_validation.py"
echo ""
echo "Ahora reinicia el servicio:"
echo "  sudo systemctl restart egarage-gunicorn.service"
echo ""
echo "NOTA: Este es un stub temporal. Para funcionalidad completa, sube el archivo"
echo "      completo desde tu máquina local usando:"
echo "      scp taller\\utils\\billing_validation.py root@159.223.200.106:/srv/egarage/taller/utils/"

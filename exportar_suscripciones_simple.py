#!/usr/bin/env python
"""
Script simple para exportar suscripciones
Ejecutar: python exportar_suscripciones_simple.py > suscripciones_export.json
"""
import os
import sys
import django
import json
from datetime import date

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.contrib.auth.models import User
from taller.models.suscripcion import Suscripcion

# Verificar cuántas suscripciones hay
total_suscripciones = Suscripcion.objects.count()
print(f"Total suscripciones encontradas: {total_suscripciones}", file=sys.stderr)

suscripciones = Suscripcion.objects.select_related("user").all()
datos_export = []

for suscripcion in suscripciones:
    try:
        user_email = suscripcion.user.email if suscripcion.user else None
        username = suscripcion.user.username if suscripcion.user else None

        dato = {
            "user_email": user_email,
            "user_username": username,
            "user_id_original": suscripcion.user.id if suscripcion.user else None,
            "tipo": suscripcion.tipo,
            "fecha_inicio": (
                suscripcion.fecha_inicio.isoformat() if suscripcion.fecha_inicio else None
            ),
            "fecha_fin": suscripcion.fecha_fin.isoformat() if suscripcion.fecha_fin else None,
            "activa": suscripcion.activa,
        }
        datos_export.append(dato)
        print(f"Exportando: {user_email} - {suscripcion.tipo}", file=sys.stderr)
    except Exception as e:
        print(f"Error procesando suscripcion {suscripcion.id}: {e}", file=sys.stderr)

resultado = {
    "total": len(datos_export),
    "fecha_exportacion": date.today().isoformat(),
    "suscripciones": datos_export,
}

print(json.dumps(resultado, indent=2, ensure_ascii=False))

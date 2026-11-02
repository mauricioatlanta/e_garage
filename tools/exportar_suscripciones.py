#!/usr/bin/env python
"""
Script para exportar suscripciones desde DigitalOcean
Ejecutar en DigitalOcean: python exportar_suscripciones.py > suscripciones_export.json
"""

import os
import django
import json
from datetime import date

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.contrib.auth.models import User
from taller.models.suscripcion import Suscripcion

def exportar_suscripciones():
    """Exporta todas las suscripciones a formato JSON"""
    suscripciones = Suscripcion.objects.select_related('user').all()
    
    datos_export = []
    
    for suscripcion in suscripciones:
        # Obtener email del usuario para hacer match después
        user_email = suscripcion.user.email if suscripcion.user else None
        username = suscripcion.user.username if suscripcion.user else None
        
        dato = {
            'user_email': user_email,
            'user_username': username,
            'user_id_original': suscripcion.user.id if suscripcion.user else None,
            'tipo': suscripcion.tipo,
            'fecha_inicio': suscripcion.fecha_inicio.isoformat() if suscripcion.fecha_inicio else None,
            'fecha_fin': suscripcion.fecha_fin.isoformat() if suscripcion.fecha_fin else None,
            'activa': suscripcion.activa,
        }
        datos_export.append(dato)
    
    # Agregar metadata
    resultado = {
        'total': len(datos_export),
        'fecha_exportacion': date.today().isoformat(),
        'suscripciones': datos_export
    }
    
    return resultado

if __name__ == '__main__':
    try:
        datos = exportar_suscripciones()
        print(json.dumps(datos, indent=2, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({'error': str(e)}, indent=2), file=__import__('sys').stderr)
        exit(1)

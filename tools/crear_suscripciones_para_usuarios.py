#!/usr/bin/env python
"""
Script para crear suscripciones para usuarios que no tienen
Ejecutar en OceanDigital: python tools/crear_suscripciones_para_usuarios.py
"""

import os
import django
from datetime import timedelta
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.contrib.auth.models import User
from taller.models.suscripcion import Suscripcion

def crear_suscripciones_faltantes():
    """Crea suscripciones trial para usuarios que no tienen"""
    
    usuarios_sin_suscripcion = User.objects.filter(suscripcion__isnull=True)
    total = usuarios_sin_suscripcion.count()
    
    if total == 0:
        print("✓ Todos los usuarios ya tienen suscripción")
        return
    
    print(f"Encontrados {total} usuarios sin suscripción")
    print("Creando suscripciones trial de 30 días...")
    print()
    
    creadas = 0
    errores = []
    
    for user in usuarios_sin_suscripcion:
        try:
            # Crear suscripción trial
            suscripcion = Suscripcion.objects.create(
                user=user,
                tipo='trial',
                fecha_inicio=timezone.now().date(),
                fecha_fin=timezone.now().date() + timedelta(days=30),
                activa=True
            )
            print(f"✓ Creada suscripción trial para {user.email}")
            creadas += 1
        except Exception as e:
            error_msg = f"Error creando suscripción para {user.email}: {e}"
            errores.append(error_msg)
            print(f"✗ {error_msg}")
    
    print()
    print("="*60)
    print("RESUMEN")
    print("="*60)
    print(f"Suscripciones creadas: {creadas}")
    print(f"Errores: {len(errores)}")
    
    if errores:
        print("\nErrores:")
        for error in errores:
            print(f"  - {error}")
    
    return creadas

if __name__ == '__main__':
    crear_suscripciones_faltantes()

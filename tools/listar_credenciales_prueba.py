#!/usr/bin/env python
"""
Script para listar las credenciales de las cuentas de prueba en eGarage.
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.contrib.auth.models import User
from taller.models.empresa import Empresa


def main():
    print("=" * 80)
    print("CREDENCIALES DE CUENTAS DE PRUEBA - eGarage")
    print("=" * 80)
    print()

    # Obtener todas las empresas con plan trial
    empresas_trial = (
        Empresa.objects.filter(plan="trial")
        .select_related("user")
        .order_by("pais", "nombre_taller")
    )

    print(f"Total de cuentas de prueba: {empresas_trial.count()}")
    print()

    for empresa in empresas_trial:
        user = empresa.user
        es_admin = user.is_superuser

        print("-" * 80)
        print(f"📋 EMPRESA: {empresa.nombre_taller}")
        print(f"   País: {empresa.pais}")
        print(f"   Username: {user.username}")
        print(f"   Email: {user.email}")
        print(f"   Nombre completo: {user.get_full_name() or 'N/A'}")
        print(f"   Tipo: {'🔑 Administrador' if es_admin else '👤 Usuario de prueba'}")
        print(f"   Plan: {empresa.plan}")
        print(f"   Suscripción activa: {'Sí' if empresa.suscripcion_activa else 'No'}")
        if empresa.fecha_fin:
            print(f"   Fecha fin: {empresa.fecha_fin.strftime('%Y-%m-%d')}")
        print()

    print("=" * 80)
    print("NOTA: Las contraseñas no se pueden recuperar por seguridad.")
    print("Si necesitas restablecer una contraseña, usa el comando:")
    print("  python manage.py changepassword <username>")
    print("=" * 80)


if __name__ == "__main__":
    main()

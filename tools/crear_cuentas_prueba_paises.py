#!/usr/bin/env python
"""
Script para crear cuentas de prueba para países faltantes en eGarage.
Crea una cuenta de usuario de prueba por país con empresa y suscripción trial.
"""

import os
import sys
import django
from datetime import timedelta

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from taller.models.empresa import Empresa
from taller.utils.pais_utils import get_configuracion_pais


# Configuración de cuentas por país
CUENTAS_PAISES = {
    "BR": {
        "username": "testuser_brasil",
        "email": "testuser@brasil-garage.com",
        "password": "Brasil2025!",
        "first_name": "Test",
        "last_name": "Brasil",
        "empresa_nombre": "Auto Shop Brasil",
        "telefono": "+5511987654321",
    },
    "MX": {
        "username": "testuser_mexico",
        "email": "testuser@mexico-garage.com",
        "password": "Mexico2025!",
        "first_name": "Test",
        "last_name": "México",
        "empresa_nombre": "Taller Mecánico México",
        "telefono": "+525512345678",
    },
    "PE": {
        "username": "testuser_peru",
        "email": "testuser@peru-garage.com",
        "password": "Peru2025!",
        "first_name": "Test",
        "last_name": "Perú",
        "empresa_nombre": "Taller Automotriz Perú",
        "telefono": "+51987654321",
    },
    "VE": {
        "username": "testuser_venezuela",
        "email": "testuser@venezuela-garage.com",
        "password": "Venezuela2025!",
        "first_name": "Test",
        "last_name": "Venezuela",
        "empresa_nombre": "Taller Mecánico Venezuela",
        "telefono": "+584123456789",
    },
}


def crear_cuenta_prueba(pais, config):
    """Crea una cuenta de prueba para un país"""
    print(f"\n{'='*80}")
    print(f"🌍 Creando cuenta de prueba para {pais}")
    print(f"{'='*80}")

    try:
        with transaction.atomic():
            # Verificar si el usuario ya existe
            if User.objects.filter(username=config["username"]).exists():
                print(f"  ⚠ Usuario {config['username']} ya existe. Omitiendo...")
                return False

            # Crear usuario
            user = User.objects.create_user(
                username=config["username"],
                email=config["email"],
                password=config["password"],
                first_name=config["first_name"],
                last_name=config["last_name"],
                is_active=True,
                is_staff=False,
                is_superuser=False,
            )
            print(f"  ✓ Usuario creado: {config['username']}")

            # Obtener configuración del país
            pais_config = get_configuracion_pais(type("TmpEmpresa", (), {"pais": pais})())

            # Crear empresa
            empresa = Empresa.objects.create(
                user=user,
                nombre_taller=config["empresa_nombre"],
                email=config["email"],
                telefono=config["telefono"],
                pais=pais,
                moneda=pais_config["moneda"],
                zona_horaria=pais_config["zona_horaria_default"],
                plan="trial",
                dias_prueba=30,
                valor_mensual=0.00,
                fecha_inicio=timezone.now(),
                fecha_fin=timezone.now() + timedelta(days=30),
                suscripcion_activa=True,
            )
            print(f"  ✓ Empresa creada: {config['empresa_nombre']}")
            print(f"  ✓ País: {pais}")
            print(f"  ✓ Moneda: {pais_config['moneda']}")
            print(f"  ✓ Plan: trial (30 días)")
            print(f"  ✓ Suscripción activa: Sí")

            return True

    except Exception as e:
        print(f"  ✗ Error al crear cuenta: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    print("=" * 80)
    print("CREACIÓN DE CUENTAS DE PRUEBA PARA PAÍSES FALTANTES")
    print("=" * 80)
    print()
    print("Países a crear:")
    for pais in CUENTAS_PAISES.keys():
        print(f"  - {pais}")
    print()

    # Crear cuentas
    creadas = 0
    omitidas = 0

    for pais, config in CUENTAS_PAISES.items():
        if crear_cuenta_prueba(pais, config):
            creadas += 1
        else:
            omitidas += 1

    print("\n" + "=" * 80)
    print("RESUMEN")
    print("=" * 80)
    print(f"Cuentas creadas: {creadas}")
    print(f"Cuentas omitidas (ya existían): {omitidas}")
    print()

    # Mostrar credenciales creadas
    print("=" * 80)
    print("CREDENCIALES CREADAS")
    print("=" * 80)

    for pais, config in CUENTAS_PAISES.items():
        # Determinar URL según país
        if pais == "BR":
            login_url = "http://127.0.0.1:8000/br/accounts/login/"
            dashboard_url = "http://127.0.0.1:8000/br/pt/dashboard/"
        elif pais == "MX":
            login_url = "http://127.0.0.1:8000/mx/accounts/login/"
            dashboard_url = "http://127.0.0.1:8000/mx/es/dashboard/"
        elif pais == "PE":
            login_url = "http://127.0.0.1:8000/pe/accounts/login/"
            dashboard_url = "http://127.0.0.1:8000/pe/es/dashboard/"
        elif pais == "VE":
            login_url = "http://127.0.0.1:8000/ve/accounts/login/"
            dashboard_url = "http://127.0.0.1:8000/ve/es/dashboard/"
        else:
            login_url = "http://127.0.0.1:8000/accounts/login/"
            dashboard_url = "http://127.0.0.1:8000/dashboard/"

        print(f"\n🌍 {pais} - {config['empresa_nombre']}")
        print(f"  👤 Username: {config['username']}")
        print(f"  📧 Email: {config['email']}")
        print(f"  🔑 Contraseña: {config['password']}")
        print(f"  🔗 Login: {login_url}")
        print(f"  📊 Dashboard: {dashboard_url}")

    print("\n" + "=" * 80)
    print("✓ Proceso completado")
    print("=" * 80)


if __name__ == "__main__":
    main()

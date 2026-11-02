#!/usr/bin/env python
"""
Script para configurar credenciales de prueba en eGarage.
- Restablece contraseñas de usuarios existentes
- Asegura un admin y una cuenta de prueba por país
- Genera lista completa de credenciales
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.contrib.auth.models import User
from django.db import transaction
from taller.models.empresa import Empresa


# Configuración de contraseñas
PASSWORDS = {
    "admin": "Admin123!",
    "contact": "Chile123!",
    "testuser_usa": "TestUSA2025!",
    "testuser_brasil": "Brasil2025!",
    "testuser_mexico": "Mexico2025!",
    "testuser_peru": "Peru2025!",
    "testuser_venezuela": "Venezuela2025!",
}


def restablecer_contraseña(user, password):
    """Restablece la contraseña de un usuario"""
    user.set_password(password)
    user.save()
    print(f"  ✓ Contraseña restablecida para {user.username}")


def main():
    print("=" * 80)
    print("CONFIGURACIÓN DE CREDENCIALES DE PRUEBA - eGarage")
    print("=" * 80)
    print()

    with transaction.atomic():
        # 1. Restablecer contraseña del admin
        try:
            admin_user = User.objects.get(username="admin")
            restablecer_contraseña(admin_user, PASSWORDS["admin"])
        except User.DoesNotExist:
            print("  ⚠ Usuario admin no existe")

        # 2. Restablecer contraseña de contact (Chile)
        try:
            contact_user = User.objects.get(username="contact")
            restablecer_contraseña(contact_user, PASSWORDS["contact"])
        except User.DoesNotExist:
            print("  ⚠ Usuario contact no existe")

        # 3. Restablecer contraseña de testuser_usa
        try:
            usa_user = User.objects.get(username="testuser_usa")
            restablecer_contraseña(usa_user, PASSWORDS["testuser_usa"])
        except User.DoesNotExist:
            print("  ⚠ Usuario testuser_usa no existe")

    print()
    print("=" * 80)
    print("LISTA COMPLETA DE CREDENCIALES")
    print("=" * 80)
    print()

    # Obtener todas las empresas trial
    empresas_trial = (
        Empresa.objects.filter(plan="trial")
        .select_related("user")
        .order_by("pais", "nombre_taller")
    )

    credenciales = []

    for empresa in empresas_trial:
        user = empresa.user
        es_admin = user.is_superuser

        # Determinar contraseña
        password = PASSWORDS.get(user.username, "CONSULTAR")

        # Determinar URL de login según país
        if empresa.pais == "CL":
            login_url = "http://127.0.0.1:8000/cl/accounts/login/"
            dashboard_url = "http://127.0.0.1:8000/cl/es/dashboard/"
        elif empresa.pais == "US":
            login_url = "http://127.0.0.1:8000/us/accounts/login/"
            dashboard_url = "http://127.0.0.1:8000/us/en/dashboard/"
        elif empresa.pais == "MX":
            login_url = "http://127.0.0.1:8000/mx/accounts/login/"
            dashboard_url = "http://127.0.0.1:8000/mx/es/dashboard/"
        elif empresa.pais == "BR":
            login_url = "http://127.0.0.1:8000/br/accounts/login/"
            dashboard_url = "http://127.0.0.1:8000/br/pt/dashboard/"
        elif empresa.pais == "PE":
            login_url = "http://127.0.0.1:8000/pe/accounts/login/"
            dashboard_url = "http://127.0.0.1:8000/pe/es/dashboard/"
        elif empresa.pais == "VE":
            login_url = "http://127.0.0.1:8000/ve/accounts/login/"
            dashboard_url = "http://127.0.0.1:8000/ve/es/dashboard/"
        else:
            login_url = "http://127.0.0.1:8000/accounts/login/"
            dashboard_url = "http://127.0.0.1:8000/dashboard/"

        credencial = {
            "tipo": "🔑 Administrador" if es_admin else "👤 Usuario de Prueba",
            "pais": empresa.pais,
            "empresa": empresa.nombre_taller,
            "username": user.username,
            "email": user.email,
            "password": password,
            "login_url": login_url,
            "dashboard_url": dashboard_url,
            "plan": empresa.plan,
            "activa": empresa.suscripcion_activa,
            "fecha_fin": empresa.fecha_fin.strftime("%Y-%m-%d") if empresa.fecha_fin else "N/A",
        }
        credenciales.append(credencial)

    # Agrupar por país
    por_pais = {}
    for cred in credenciales:
        pais = cred["pais"]
        if pais not in por_pais:
            por_pais[pais] = []
        por_pais[pais].append(cred)

    # Mostrar credenciales agrupadas por país
    for pais in sorted(por_pais.keys()):
        print(f"\n{'='*80}")
        print(f"🌍 PAÍS: {pais}")
        print(f"{'='*80}")

        for cred in por_pais[pais]:
            print(f"\n{cred['tipo']}")
            print(f"  📋 Empresa: {cred['empresa']}")
            print(f"  👤 Username: {cred['username']}")
            print(f"  📧 Email: {cred['email']}")
            print(f"  🔑 Contraseña: {cred['password']}")
            print(f"  🔗 Login: {cred['login_url']}")
            print(f"  📊 Dashboard: {cred['dashboard_url']}")
            print(
                f"  📅 Plan: {cred['plan']} | Activa: {'Sí' if cred['activa'] else 'No'} | Fin: {cred['fecha_fin']}"
            )

    # Resumen
    print("\n" + "=" * 80)
    print("RESUMEN")
    print("=" * 80)
    print(f"Total de cuentas: {len(credenciales)}")
    print(f"Países: {len(por_pais)}")
    print(f"  - Administradores: {sum(1 for c in credenciales if 'Administrador' in c['tipo'])}")
    print(f"  - Usuarios de prueba: {sum(1 for c in credenciales if 'Usuario' in c['tipo'])}")
    print()

    # Guardar en archivo
    archivo_credenciales = "CREDENCIALES_PRUEBA.md"
    with open(archivo_credenciales, "w", encoding="utf-8") as f:
        f.write("# 🔐 CREDENCIALES DE PRUEBA - eGarage\n\n")
        f.write(
            "**Fecha de generación:** "
            + str(django.utils.timezone.now().strftime("%Y-%m-%d %H:%M:%S"))
            + "\n\n"
        )
        f.write("---\n\n")

        for pais in sorted(por_pais.keys()):
            f.write(f"## 🌍 {pais}\n\n")
            for cred in por_pais[pais]:
                f.write(f"### {cred['tipo']} - {cred['empresa']}\n\n")
                f.write(f"- **Username:** `{cred['username']}`\n")
                f.write(f"- **Email:** `{cred['email']}`\n")
                f.write(f"- **Contraseña:** `{cred['password']}`\n")
                f.write(f"- **Login URL:** {cred['login_url']}\n")
                f.write(f"- **Dashboard URL:** {cred['dashboard_url']}\n")
                f.write(f"- **Plan:** {cred['plan']}\n")
                f.write(f"- **Activa:** {'Sí' if cred['activa'] else 'No'}\n")
                f.write(f"- **Fecha fin:** {cred['fecha_fin']}\n\n")

        f.write("---\n\n")
        f.write("## 📊 Resumen\n\n")
        f.write(f"- Total de cuentas: {len(credenciales)}\n")
        f.write(f"- Países: {len(por_pais)}\n")
        f.write(
            f"- Administradores: {sum(1 for c in credenciales if 'Administrador' in c['tipo'])}\n"
        )
        f.write(f"- Usuarios de prueba: {sum(1 for c in credenciales if 'Usuario' in c['tipo'])}\n")

    print(f"✓ Credenciales guardadas en: {archivo_credenciales}")
    print("=" * 80)


if __name__ == "__main__":
    main()

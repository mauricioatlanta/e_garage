#!/usr/bin/env python
"""
Script para verificar y corregir el país de usuarios de USA en el servidor
Uso: python corregir_pais_usuario_usa.py [username]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")

import django

django.setup()

from django.contrib.auth import get_user_model
from taller.models import Empresa

User = get_user_model()

print("=" * 70)
print("VERIFICACIÓN Y CORRECCIÓN DE PAÍS DE USUARIOS USA")
print("=" * 70)

# Si se pasa un username como argumento, verificar solo ese usuario
username = sys.argv[1] if len(sys.argv) > 1 else None

if username:
    try:
        user = User.objects.get(username=username)
        usuarios = [user]
        print(f"\nVerificando usuario específico: {username}\n")
    except User.DoesNotExist:
        print(f"❌ Usuario '{username}' no encontrado")
        sys.exit(1)
else:
    # Verificar todos los usuarios con empresa
    usuarios = User.objects.filter(empresa__isnull=False).select_related("empresa")
    print(f"\nVerificando todos los usuarios con empresa ({usuarios.count()} usuarios)\n")

usuarios_corregidos = []
usuarios_problema = []

for user in usuarios:
    empresa = user.empresa if hasattr(user, "empresa") else None

    if not empresa:
        print(f"⚠️  {user.username}: No tiene empresa asociada")
        continue

    pais_actual = empresa.pais
    print(f"Usuario: {user.username}")
    print(f"  Email: {user.email}")
    print(f"  Empresa: {empresa.nombre_taller}")
    print(f"  País actual: {pais_actual}")

    # Detectar país correcto basado en email o nombre de empresa
    pais_correcto = None

    # Detectar por email
    if "@" in user.email:
        email_domain = user.email.lower()
        if "usa" in email_domain or "us" in email_domain or "usa-garage" in email_domain:
            pais_correcto = "US"
        elif "egarage.cl" in email_domain or "chile" in email_domain:
            pais_correcto = "CL"

    # Detectar por nombre de empresa
    if not pais_correcto and empresa.nombre_taller:
        nombre_lower = empresa.nombre_taller.lower()
        if "usa" in nombre_lower or "united states" in nombre_lower or "angel auto" in nombre_lower:
            pais_correcto = "US"
        elif "chile" in nombre_lower or "chileno" in nombre_lower:
            pais_correcto = "CL"

    # Si no se puede detectar, preguntar o usar el actual
    if not pais_correcto:
        print(f"  ⚠️  No se pudo detectar país automáticamente")
        usuarios_problema.append((user, empresa, pais_actual))
    elif pais_correcto != pais_actual:
        print(f"  ❌ País incorrecto. Debería ser: {pais_correcto}")
        print(f"  🔧 Corrigiendo...")
        empresa.pais = pais_correcto
        empresa.save()
        print(f"  ✅ País actualizado a: {empresa.pais}")
        usuarios_corregidos.append((user, pais_actual, pais_correcto))
    else:
        print(f"  ✅ País correcto")

    print()

# Resumen
print("=" * 70)
print("RESUMEN")
print("=" * 70)
print(f"Usuarios corregidos: {len(usuarios_corregidos)}")
if usuarios_corregidos:
    print("\nCorrecciones realizadas:")
    for user, pais_anterior, pais_nuevo in usuarios_corregidos:
        print(f"  - {user.username}: {pais_anterior} → {pais_nuevo}")

print(f"\nUsuarios con problemas (requieren revisión manual): {len(usuarios_problema)}")
if usuarios_problema:
    print("\nUsuarios que requieren revisión:")
    for user, empresa, pais_actual in usuarios_problema:
        print(f"  - {user.username} ({user.email})")
        print(f"    Empresa: {empresa.nombre_taller}")
        print(f"    País actual: {pais_actual}")

print("\n" + "=" * 70)
print("FIN")
print("=" * 70)
print("\n💡 Si corrigiste usuarios, reinicia el servidor web para que los cambios surtan efecto.")

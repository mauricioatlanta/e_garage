#!/usr/bin/env python
import os
import sys

import django

# Configurar Django
sys.path.append(".")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.contrib.auth.models import User

from taller.models.clientes import Cliente
from taller.models.empresa import Empresa

# Verificar la relación usuario-empresa-cliente
print("=== VERIFICACIÓN DE RELACIONES ===")

# Usuario admin
user = User.objects.get(username="admin")
print(f"Usuario: {user.username}")
print(f"Empresa del usuario: {user.empresa}")
print(
    f"País de la empresa del usuario: {user.empresa.pais if user.empresa else 'None'}"
)

# Cliente 1
cliente = Cliente.objects.get(id=1)
print(f"\nCliente 1: {cliente.nombre} {cliente.apellido}")
print(f"Empresa del cliente: {cliente.empresa}")
print(f"País de la empresa del cliente: {cliente.empresa.pais}")

# Verificar si el TenantViewMixin permitiría al usuario ver este cliente
print(f"\n=== FILTRADO TENANT ===")
print(f"¿Usuario empresa == Cliente empresa? {user.empresa == cliente.empresa}")

# Filtrar clientes como lo haría TenantViewMixin
if user.empresa:
    clientes_accesibles = Cliente.objects.filter(empresa=user.empresa)
    print(f"Clientes accesibles para el usuario: {clientes_accesibles.count()}")
    for c in clientes_accesibles:
        print(f"  - Cliente {c.id}: {c.nombre} {c.apellido}")

    if cliente in clientes_accesibles:
        print("✅ El cliente 1 ES accesible para el usuario admin")
    else:
        print("❌ El cliente 1 NO es accesible para el usuario admin")
else:
    print("❌ Usuario sin empresa - no puede acceder a ningún cliente")

#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from taller.models import Documento, Empresa, Cliente, Vehiculo
from django.contrib.auth.models import User

# Buscar empresa chilena
empresa = Empresa.objects.filter(pais='CL').first()
if not empresa:
    print("❌ No hay empresa chilena")
    exit(1)

print(f"Empresa: {empresa.nombre_taller} ({empresa.pais})")

# Buscar cliente y vehículo
cliente = Cliente.objects.filter(empresa=empresa).first()
vehiculo = Vehiculo.objects.filter(empresa=empresa).first()
user = User.objects.first()

print(f"Cliente: {cliente.nombre if cliente else 'N/A'}")
print(f"Vehículo: {vehiculo.marca}-{vehiculo.modelo}" if vehiculo else "Vehículo: N/A")

# Crear documento
doc = Documento.objects.create(
    tipo='PRES',
    numero=99,
    empresa=empresa,
    cliente=cliente,
    vehiculo=vehiculo,
    usuario_creacion=user
)

print(f"✅ Documento creado: {doc.pk} - {doc.tipo}-{doc.numero} (Empresa: {doc.empresa.pais})")

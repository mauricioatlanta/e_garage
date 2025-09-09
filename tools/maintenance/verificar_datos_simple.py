"""
Script simple para verificar y crear datos básicos
"""

import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings_sqlite")
django.setup()


from taller.models.clientes import Cliente
from taller.models.documento import Documento
from taller.models.empresa import Empresa

print("=== VERIFICANDO DATOS ===")

# Verificar empresas
empresas = Empresa.objects.all()
print(f"Empresas existentes: {empresas.count()}")
for emp in empresas:
    print(f"  - {emp.nombre_taller} ({emp.pais})")

# Verificar documentos
documentos = Documento.objects.all()
print(f"Documentos existentes: {documentos.count()}")
for doc in documentos:
    print(f"  - ID: {doc.id}, Tipo: {doc.tipo}, Número: {doc.numero}")

# Si no hay datos, crear empresa y documento básico
if empresas.count() == 0:
    print("Creando empresa de prueba...")
    empresa = Empresa.objects.create(
        nombre_taller="Taller Demo Chile", pais="CL", ciudad="Santiago"
    )

    cliente = Cliente.objects.create(
        empresa=empresa, nombre="Cliente Demo", email="demo@test.com"
    )

    documento = Documento.objects.create(
        empresa=empresa, cliente=cliente, tipo="PRES", numero=1, total=100000
    )

    print(f"Documento creado con ID: {documento.id}")

print("=== FIN VERIFICACIÓN ===")

#!/usr/bin/env python
import os

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()


from taller.models import *

print("=== REVISIÓN DE MODELOS PARA DASHBOARD DE EMPRESA ===")
print()

# Verificar qué modelos existen
print("📊 MODELOS PRINCIPALES:")
try:
    print(f"✅ Empresa: {Empresa.objects.count()} registros")
except:
    print("❌ Modelo Empresa no disponible")

try:
    print(f"✅ Documento: {Documento.objects.count()} registros")
except:
    print("❌ Modelo Documento no disponible")

try:
    print(f"✅ Cliente: {Cliente.objects.count()} registros")
except:
    print("❌ Modelo Cliente no disponible")

try:
    print(f"✅ Tecnico: {Tecnico.objects.count()} registros")
except:
    print("❌ Modelo Tecnico no disponible")

try:
    print(f"✅ Vehiculo: {Vehiculo.objects.count()} registros")
except:
    print("❌ Modelo Vehiculo no disponible")

from taller.models.lineas_documento import LineaServicio

try:
    print(f"✅ LineaServicio: {LineaServicio.objects.count()} registros")
except:
    print("❌ Modelo LineaServicio no disponible")

try:
    print(f"✅ Repuesto: {Repuesto.objects.count()} registros")
except:
    print("❌ Modelo Repuesto no disponible")

print()
print("🏢 EMPRESAS REGISTRADAS:")
for empresa in Empresa.objects.all()[:10]:
    print(f"- {empresa.nombre_taller} ({empresa.pais}) - Usuario: {empresa.user.username}")

print()
print("📈 DATOS PARA DASHBOARD (últimos 5 documentos):")
for doc in Documento.objects.select_related("empresa", "cliente", "tecnico").all()[:5]:
    print(
        f"- Doc #{doc.id}: {doc.tipo_documento} - Cliente: {doc.cliente} - Técnico: {doc.tecnico} - Empresa: {doc.empresa.nombre_taller}"
    )

print()
print("⚙️ SERVICIOS MÁS POPULARES:")
from django.db.models import Count

servicios_top = (
    LineaServicio.objects.values("nombre").annotate(total=Count("id")).order_by("-total")[:5]
)

for servicio in servicios_top:
    print(f"- {servicio['nombre']}: {servicio['total']} veces")

print()
print("🔧 TÉCNICOS MÁS ACTIVOS:")
tecnicos_activos = Tecnico.objects.annotate(docs_count=Count("documentos")).order_by("-docs_count")[
    :5
]

for tecnico in tecnicos_activos:
    print(f"- {tecnico.nombre} ({tecnico.empresa.nombre_taller}): {tecnico.docs_count} documentos")

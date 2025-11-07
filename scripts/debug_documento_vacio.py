#!/usr/bin/env python
import os
import sys

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings_sqlite")
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth.models import User

from taller.models.documento import (Documento, RepuestoDocumento,
                                     ServicioDocumento)
from taller.models.empresa import Empresa

print("=== DEBUG DOCUMENTO VACÍO ===")

# Obtener último documento creado
ultimo_doc = Documento.objects.order_by("-id").first()
if not ultimo_doc:
    print("❌ No hay documentos en la base de datos")
    sys.exit(1)

print(
    f"📄 Último documento: {ultimo_doc.numero_documento} ({ultimo_doc.tipo_documento})"
)
print(f"   Cliente: {ultimo_doc.cliente}")
print(f"   Empresa: {ultimo_doc.empresa}")
print(f"   Fecha: {ultimo_doc.fecha}")

# Verificar repuestos
repuestos = RepuestoDocumento.objects.filter(documento=ultimo_doc)
print(f"\n🔧 Repuestos encontrados: {repuestos.count()}")
for rep in repuestos:
    print(f"   - {rep.nombre} (${rep.precio} x {rep.cantidad} = ${rep.total})")

# Verificar servicios
servicios = ServicioDocumento.objects.filter(documento=ultimo_doc)
print(f"\n⚙️ Servicios encontrados: {servicios.count()}")
for serv in servicios:
    print(f"   - {serv.nombre} (${serv.precio})")

# Verificar todos los repuestos y servicios recientes
print(f"\n📊 ESTADÍSTICAS GENERALES:")
print(f"   Total documentos: {Documento.objects.count()}")
print(f"   Total repuestos en documentos: {RepuestoDocumento.objects.count()}")
print(f"   Total servicios en documentos: {ServicioDocumento.objects.count()}")

# Verificar últimos 5 documentos
print(f"\n📋 ÚLTIMOS 5 DOCUMENTOS:")
ultimos = Documento.objects.order_by("-id")[:5]
for doc in ultimos:
    rep_count = RepuestoDocumento.objects.filter(documento=doc).count()
    serv_count = ServicioDocumento.objects.filter(documento=doc).count()
    print(f"   {doc.numero_documento}: {rep_count} repuestos, {serv_count} servicios")

# Verificar si hay problemas de empresa/multiempresa
print(f"\n🏢 VERIFICACIÓN MULTIEMPRESA:")
empresas = Empresa.objects.all()
for empresa in empresas:
    docs_empresa = Documento.objects.filter(empresa=empresa).count()
    print(f"   {empresa.nombre_taller}: {docs_empresa} documentos")

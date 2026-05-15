#!/usr/bin/env python
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from taller.models import Documento

print("=== DOCUMENTOS DISPONIBLES ===")
docs = Documento.objects.all()
print(f"Total: {docs.count()} documentos")

for d in docs:
    empresa_nombre = d.empresa.nombre_taller if d.empresa else "N/A"
    empresa_pais = d.empresa.pais if d.empresa else "N/A"
    print(f"  {d.pk:2d} - {d.tipo}-{d.numero:3d} | Empresa: {empresa_nombre} ({empresa_pais})")

print("\n=== ANÁLISIS ===")
print(f"IDs existentes: {list(docs.values_list('pk', flat=True))}")
print("Documento 45 existe:", Documento.objects.filter(pk=45).exists())
print("Documento 40 existe:", Documento.objects.filter(pk=40).exists())

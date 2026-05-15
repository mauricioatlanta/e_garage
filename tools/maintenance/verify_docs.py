#!/usr/bin/env python3
import os
import sys

import django

# Configurar Django
sys.path.append("E:/projecto/e_garage")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.contrib.auth.models import User

from taller.models.documento import Documento

# Verificar datos
user = User.objects.get(username="testuser_usa")
empresa = user.empresa

print(f"🏢 Empresa: {empresa.nombre_taller}")

# Obtener documentos de la empresa
documentos = Documento.objects.filter(empresa=empresa).order_by("-fecha_emision", "-id")
print(f"📄 Total documentos encontrados: {documentos.count()}")

print()
print("📋 Lista de documentos:")
for doc in documentos[:5]:  # Solo los primeros 5
    print(
        f"   {doc.numero_documento} - {doc.get_tipo_display()} - {doc.cliente} - {doc.fecha_emision} - ${doc.total}"
    )

print(f"\n✅ Vista debería mostrar {documentos.count()} documentos")

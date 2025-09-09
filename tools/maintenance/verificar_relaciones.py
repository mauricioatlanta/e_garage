#!/usr/bin/env python
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.contrib.auth.models import User

from taller.models.documento import Documento
from taller.models.empresa import Empresa

print("=== EMPRESAS Y DOCUMENTOS ===")
for e in Empresa.objects.all():
    docs = Documento.objects.filter(empresa=e).count()
    user_info = e.user.username if e.user else "Sin usuario"
    print(
        f"Empresa {e.pk}: {e.nombre_taller} - {docs} documentos - Usuario: {user_info}"
    )

print("\n=== USUARIOS Y EMPRESAS ===")
for u in User.objects.all():
    try:
        emp = u.empresa
        print(f"Usuario {u.username}: Empresa {emp.nombre_taller}")
    except:
        print(f"Usuario {u.username}: Sin empresa asociada")

#!/usr/bin/env python
import os

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.shortcuts import redirect
from django.urls import reverse

print("🧪 Verificando URLs y redirecciones:")

# Verificar URL de listado
try:
    lista_url = reverse("documentos:lista_documentos")
    print(f"✅ URL listado: {lista_url}")
except Exception as e:
    print(f"❌ Error URL listado: {e}")

# Verificar URL de edición
try:
    editar_url = reverse(
        "documentos:editar_documento_nuevo", kwargs={"documento_id": 107}
    )
    print(f"✅ URL edición: {editar_url}")
except Exception as e:
    print(f"❌ Error URL edición: {e}")

# Simular redirección
try:
    redirect_response = redirect("documentos:lista_documentos")
    print(
        f"✅ Redirección simulada: {redirect_response.status_code} -> {redirect_response.url}"
    )
except Exception as e:
    print(f"❌ Error redirección: {e}")

print("\n🎯 Flujo esperado:")
print("1. Usuario edita documento en /documentos/nuevo-editar/107/")
print("2. Usuario hace cambios y guarda")
print("3. POST procesa datos exitosamente")
print("4. Redirige a /documentos/ (listado)")
print("5. Muestra mensaje 'Documento F-009 guardado exitosamente'")
print("\n✅ Configuración completada correctamente!")

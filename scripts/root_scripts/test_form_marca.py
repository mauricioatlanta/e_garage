# -*- coding: utf-8 -*-
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from taller.vehiculos.forms import VehiculoForm

User = get_user_model()

# Crear un request simulado para /us/vehiculos/crear/
factory = RequestFactory()
request = factory.get("/us/vehiculos/crear/")

# Obtener un usuario (ajusta esto según tu base de datos)
try:
    user = User.objects.first()
    if not user:
        print("No hay usuarios en la base de datos")
        exit(1)
except Exception as e:
    print(f"Error al obtener usuario: {e}")
    exit(1)

print("=" * 60)
print("TEST: Formulario VehiculoForm para USA")
print("=" * 60)
print(f"Usuario: {user.username}")
print(f"Empresa: {getattr(user, 'empresa', None)}")
print(f"País empresa: {getattr(getattr(user, 'empresa', None), 'pais', 'N/A')}")
print(f"Path request: {request.path}")
print()

# Crear el formulario
print("Creando formulario...")
form = VehiculoForm(user=user, request=request)

print("\n" + "=" * 60)
print("VERIFICACION DEL CAMPO MARCA")
print("=" * 60)

if "marca" in form.fields:
    marca_field = form.fields["marca"]
    print(f"✅ Campo marca existe")
    print(f"   Tipo: {type(marca_field).__name__}")
    print(f"   Label: {marca_field.label}")
    print(f"   Required: {marca_field.required}")

    if hasattr(marca_field, "choices"):
        choices = marca_field.choices
        print(f"   Choices: {len(choices)} opciones")
        if len(choices) > 1:
            print(f"\n   Primeras 10 opciones:")
            for i, (value, label) in enumerate(choices[:10], 1):
                print(f"     {i}. value='{value}' -> label='{label}'")
            if len(choices) > 10:
                print(f"     ... y {len(choices) - 10} más")
        else:
            print(f"   ⚠️ PROBLEMA: Solo tiene 1 opción: {choices}")

    elif hasattr(marca_field, "queryset"):
        qs = marca_field.queryset
        count = qs.count()
        print(f"   Queryset: {count} marcas")
        if count > 0:
            print(f"\n   Primeras 10 marcas:")
            for i, marca in enumerate(qs[:10], 1):
                print(f"     {i}. {marca.nombre} (ID: {marca.id})")
        else:
            print(f"   ⚠️ PROBLEMA: Queryset vacío")
else:
    print("❌ Campo marca NO existe en el formulario")

print("\n" + "=" * 60)
print("RENDERIZADO HTML DEL CAMPO")
print("=" * 60)
if "marca" in form.fields:
    html = str(form["marca"])
    # Contar opciones en el HTML
    option_count = html.count("<option")
    print(f"Opciones en HTML: {option_count}")
    print(f"\nHTML (primeros 500 caracteres):")
    print(html[:500])
    if len(html) > 500:
        print("...")

print("\n" + "=" * 60)

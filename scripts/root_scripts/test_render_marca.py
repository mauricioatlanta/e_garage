# -*- coding: utf-8 -*-
import os
import django
import re

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from django.template import Context, Template
from taller.vehiculos.forms import VehiculoForm

User = get_user_model()

# Crear un request simulado
factory = RequestFactory()
request = factory.get("/us/vehiculos/crear/")

# Obtener usuario
user = User.objects.first()

print("=" * 60)
print("TEST: Renderizado HTML del campo marca")
print("=" * 60)

# Crear formulario
form = VehiculoForm(user=user, request=request)

# Verificar campo
if "marca" in form.fields:
    marca_field = form.fields["marca"]
    print(f"Tipo: {type(marca_field).__name__}")
    print(f"Choices: {len(marca_field.choices)} opciones")
    print(f"Primeras 5 choices: {list(marca_field.choices[:5])}")

    # Renderizar HTML
    t = Template("{{ form.marca }}")
    c = Context({"form": form})
    html = t.render(c)

    print(f"\nHTML renderizado (primeros 500 chars):")
    print(html[:500])

    # Contar opciones en HTML
    options = re.findall(r"<option[^>]*>.*?</option>", html, re.DOTALL)
    print(f"\nOpciones en HTML: {len(options)}")
    for i, opt in enumerate(options[:10], 1):
        print(f"  {i}. {opt[:100]}")

    if len(options) != len(marca_field.choices):
        print(
            f"\n❌ PROBLEMA: Choices tiene {len(marca_field.choices)} pero HTML solo tiene {len(options)}"
        )
    else:
        print(f"\n✅ HTML tiene {len(options)} opciones correctamente")
else:
    print("❌ Campo marca no existe")

print("=" * 60)

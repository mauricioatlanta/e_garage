# -*- coding: utf-8 -*-
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.test import RequestFactory
from django.contrib.auth import get_user_model
from django.template import Context, Template
from taller.vehiculos.forms import VehiculoForm

User = get_user_model()

# Crear request simulado
factory = RequestFactory()
request = factory.get("/us/vehiculos/crear/")
user = User.objects.first()

print("=" * 60)
print("TEST: Renderizado del template")
print("=" * 60)

# Crear formulario
form = VehiculoForm(user=user, request=request)

# Template con renderizado manual
template_str = """
{% if form.marca.field.choices %}
  <select name="marca" id="id_marca" required>
    {% for value, label in form.marca.field.choices %}
      <option value="{{ value }}">{{ label }}</option>
    {% endfor %}
  </select>
  DEBUG: Choices={{ form.marca.field.choices|length }}
{% else %}
  NO HAY CHOICES
{% endif %}
"""

t = Template(template_str)
c = Context({"form": form})
html = t.render(c)

print("HTML renderizado:")
print(html[:500])
print()

# Contar opciones en el HTML
import re

options = re.findall(r"<option[^>]*>.*?</option>", html, re.DOTALL)
print(f"Opciones encontradas en HTML: {len(options)}")
for i, opt in enumerate(options[:5], 1):
    print(f"  {i}. {opt[:80]}")

print("=" * 60)

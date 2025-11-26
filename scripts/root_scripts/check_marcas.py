# -*- coding: utf-8 -*-
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from taller.models.marca import Marca

print("=" * 60)
print("VERIFICACION DE MARCAS PARA USA")
print("=" * 60)

# Verificar marcas en modelo Marca
print("\n1. MARCAS EN MODELO Marca CON country='US':")
marcas_usa = Marca.objects.filter(country="US").order_by("nombre")
total = marcas_usa.count()
print(f"Total: {total}")

if total > 0:
    print("\nPrimeras 20:")
    for i, m in enumerate(marcas_usa[:20], 1):
        print(f"  {i}. {m.nombre} (ID: {m.id})")
else:
    print("NO HAY MARCAS")

# Verificar catalogo
print("\n2. MARCAS EN CATALOGO:")
try:
    from taller.models.catalogo import CatalogoModeloAuto

    marcas_cat = list(CatalogoModeloAuto.get_marcas_activas()[:500])
    print(f"Total: {len(marcas_cat)}")
    if len(marcas_cat) > 0:
        print("\nPrimeras 20:")
        for i, m in enumerate(marcas_cat[:20], 1):
            print(f"  {i}. {m}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)

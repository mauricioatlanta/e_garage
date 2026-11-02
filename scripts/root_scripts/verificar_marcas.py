import django
import os
import sys

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(__file__))

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from taller.models.marca import Marca

print("=" * 60)
print("VERIFICACION DE MARCAS PARA USA")
print("=" * 60)

# 1. Verificar marcas en modelo Marca
print('\n1. MARCAS EN MODELO Marca CON country="US":')
marcas_usa = Marca.objects.filter(country="US").order_by("nombre")
total_marcas = marcas_usa.count()
print(f"Total: {total_marcas} marcas")

if total_marcas > 0:
    print("\nPrimeras 20 marcas:")
    for i, marca in enumerate(marcas_usa[:20], 1):
        print(f"  {i}. {marca.nombre} (ID: {marca.id})")
    if total_marcas > 20:
        print(f"  ... y {total_marcas - 20} mas")
else:
    print('NO HAY MARCAS en el modelo Marca con country="US"')

# 2. Verificar catalogo
print("\n2. MARCAS EN CATALOGO (CatalogoModeloAuto):")
try:
    from taller.models.catalogo import CatalogoModeloAuto

    marcas_catalogo = CatalogoModeloAuto.get_marcas_activas()
    marcas_list = list(marcas_catalogo[:500])
    total_catalogo = len(marcas_list)
    print(f"Total: {total_catalogo} marcas")

    if total_catalogo > 0:
        print("\nPrimeras 20 marcas:")
        for i, marca in enumerate(marcas_list[:20], 1):
            print(f"  {i}. {marca}")
        if total_catalogo > 20:
            print(f"  ... y {total_catalogo - 20} mas")
    else:
        print("NO HAY MARCAS en el catalogo")

    # Total de registros
    total_registros = CatalogoModeloAuto.objects.filter(activo=True).count()
    print(f"\nTotal de registros activos: {total_registros}")
except ImportError:
    print("El modelo CatalogoModeloAuto no existe")
except Exception as e:
    print(f"Error: {e}")

# 3. Resumen por pais
print("\n3. RESUMEN POR PAIS:")
for country in ["US", "CL", "MX"]:
    count = Marca.objects.filter(country=country).count()
    print(f"  {country}: {count} marcas")

print("\n" + "=" * 60)

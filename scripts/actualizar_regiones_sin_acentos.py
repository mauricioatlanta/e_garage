import os
import django
import sys

# Configura el entorno Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from taller.models.region_ciudad import TallerRegion

def quitar_acentos(texto):
    reemplazos = (
        ('á', 'a'), ('é', 'e'), ('í', 'i'), ('ó', 'o'), ('ú', 'u'),
        ('Á', 'A'), ('É', 'E'), ('Í', 'I'), ('Ó', 'O'), ('Ú', 'U'),
        ('ñ', 'n'), ('Ñ', 'N'), ('ü', 'u'), ('Ü', 'U')
    )
    for a, b in reemplazos:
        texto = texto.replace(a, b)
    return texto

for region in TallerRegion.objects.all():
    nombre_original = region.nombre
    nombre_sin_acentos = quitar_acentos(nombre_original)
    if nombre_original != nombre_sin_acentos:
        region.nombre = nombre_sin_acentos
        region.save()
        print(f"Actualizada: {nombre_original} -> {nombre_sin_acentos}")
    else:
        print(f"Sin cambios: {nombre_original}")

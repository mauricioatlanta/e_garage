from taller.models.region_ciudad import TallerRegion

regiones = [
    "Arica y Parinacota",
    "Tarapacá",
    "Antofagasta",
    "Atacama",
    "Coquimbo",
    "Valparaíso",
    "Metropolitana de Santiago",
    "Libertador General Bernardo O'Higgins",
    "Maule",
    "Ñuble",
    "Biobío",
    "La Araucanía",
    "Los Ríos",
    "Los Lagos",
    "Aysén del General Carlos Ibáñez del Campo",
    "Magallanes y de la Antártica Chilena"
]

for nombre in regiones:
    obj, created = TallerRegion.objects.get_or_create(nombre=nombre)
    print(f"{'Creada' if created else 'Existente'}: {nombre}")

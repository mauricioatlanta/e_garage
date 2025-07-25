
# -*- coding: utf-8 -*-
import os
import django
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()
from taller.models.region_ciudad import TallerRegion, TallerCiudad

ciudades_por_region = {
    "Arica y Parinacota": [
        "Arica", "Putre", "General Lagos", "Camarones", "Codpa", "Chitita", "Visviri", "Belen", "Guallatire", "Ticnamar"
    ],
    "Tarapaca": [
        "Iquique", "Alto Hospicio", "Pozo Almonte", "Pica", "Huara", "Camina", "Colchane", "La Tirana", "Matilla", "Mamina"
    ],
    "Antofagasta": [
        "Antofagasta", "Calama", "Mejillones", "Tocopilla", "Taltal", "Sierra Gorda", "Maria Elena", "Ollague", "San Pedro de Atacama", "Quillagua"
    ],
    "Atacama": [
        "Copiapo", "Vallenar", "Caldera", "Chanaral", "El Salvador", "Tierra Amarilla", "Diego de Almagro", "Freirina", "Huasco", "Alto del Carmen"
    ],
    "Coquimbo": [
        "La Serena", "Coquimbo", "Ovalle", "Illapel", "Los Vilos", "Salamanca", "Andacollo", "Combarbala", "Monte Patria", "Punitaqui"
    ],
    "Valparaiso": [
        "Valparaiso", "Vina del Mar", "Quillota", "San Antonio", "San Felipe", "Los Andes", "La Calera", "La Ligua", "Quilpue", "Villa Alemana"
    ],
    "Metropolitana de Santiago": [
        "Santiago", "Puente Alto", "Maipu", "La Florida", "Las Condes", "San Bernardo", "Penalolen", "Pudahuel", "Quilicura", "Lo Barnechea"
    ],
    "Libertador General Bernardo O'Higgins": [
        "Rancagua", "San Fernando", "Santa Cruz", "Pichilemu", "Chimbarongo", "San Vicente", "Peumo", "Rengo", "Graneros", "Machali"
    ],
    "Maule": [
        "Talca", "Curico", "Linares", "Cauquenes", "Constitucion", "Parral", "San Javier", "Molina", "Longavi", "Teno"
    ],
    "Nuble": [
        "Chillan", "San Carlos", "Bulnes", "Quirihue", "Coelemu", "Yungay", "El Carmen", "Pemuco", "Trehuaco", "Cobquecura"
    ],
    "Biobio": [
        "Concepcion", "Los Angeles", "Coronel", "Talcahuano", "Chiguayante", "Hualpen", "Lota", "San Pedro de la Paz", "Arauco", "Canete"
    ],
    "La Araucania": [
        "Temuco", "Villarrica", "Angol", "Pucon", "Padre Las Casas", "Nueva Imperial", "Lautaro", "Gorbea", "Carahue", "Loncoche"
    ],
    "Los Rios": [
        "Valdivia", "La Union", "Rio Bueno", "Panguipulli", "Futrono", "Lago Ranco", "Paillaco", "Los Lagos", "Mafil", "Corral"
    ],
    "Los Lagos": [
        "Puerto Montt", "Osorno", "Castro", "Ancud", "Purranque", "Frutillar", "Llanquihue", "Calbuco", "Quellon", "Puerto Varas"
    ],
    "Aysen del General Carlos Ibanez del Campo": [
        "Coyhaique", "Puerto Aysen", "Chile Chico", "Cochrane", "Puerto Cisnes", "Rio Ibanez", "Lago Verde", "Guaitecas", "Tortel", "Villa OHiggins"
    ],
    "Magallanes y de la Antartica Chilena": [
        "Punta Arenas", "Puerto Natales", "Porvenir", "Cabo de Hornos", "Primavera", "San Gregorio", "Laguna Blanca", "Rio Verde", "Timaukel", "Torres del Paine"
    ]
}

for region_nombre, ciudades in ciudades_por_region.items():
    region = TallerRegion.objects.filter(nombre=region_nombre).first()
    if region:
        for ciudad_nombre in ciudades:
            obj, created = TallerCiudad.objects.get_or_create(nombre=ciudad_nombre, region=region)
            print(f"{'Creada' if created else 'Existente'}: {ciudad_nombre} en {region_nombre}")
# -*- coding: utf-8 -*-
from taller.models.region_ciudad import TallerRegion, TallerCiudad

ciudades_por_region = {
    "Arica y Parinacota": ["Arica", "Putre"],
    "Tarapacá": ["Iquique", "Alto Hospicio"],
    "Antofagasta": ["Antofagasta", "Calama", "Mejillones"],
    "Atacama": ["Copiapó", "Vallenar"],
    "Coquimbo": ["La Serena", "Coquimbo", "Ovalle"],
    "Valparaíso": ["Valparaíso", "Viña del Mar", "Quillota"],
    "Metropolitana de Santiago": ["Santiago", "Puente Alto", "Maipú"],
    "Libertador General Bernardo O'Higgins": ["Rancagua", "San Fernando"],
    "Maule": ["Talca", "Curicó", "Linares"],
    "Ñuble": ["Chillán", "San Carlos"],
    "Biobío": ["Concepción", "Los Ángeles", "Coronel"],
    "La Araucanía": ["Temuco", "Villarrica"],
    "Los Ríos": ["Valdivia", "La Unión"],
    "Los Lagos": ["Puerto Montt", "Osorno", "Castro"],
    "Aysén del General Carlos Ibáñez del Campo": ["Coyhaique", "Puerto Aysén"],
    "Magallanes y de la Antártica Chilena": ["Punta Arenas", "Puerto Natales"]
}

for region_nombre, ciudades in ciudades_por_region.items():
    region = TallerRegion.objects.filter(nombre=region_nombre).first()
    if region:
        for ciudad_nombre in ciudades:
            obj, created = TallerCiudad.objects.get_or_create(nombre=ciudad_nombre, region=region)
            print(f"{'Creada' if created else 'Existente'}: {ciudad_nombre} en {region_nombre}")

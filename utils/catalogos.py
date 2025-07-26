# utils/catalogos.py

CATALOGOS_REGIONES = {
    'CL': [
        'Región Metropolitana', 'Valparaíso', 'Biobío', 'Araucanía', 'Antofagasta', 'Maule', 'O’Higgins', 'Los Lagos', 'Coquimbo', 'Los Ríos', 'Tarapacá', 'Atacama', 'Magallanes', 'Arica y Parinacota', 'Ñuble', 'Aysén'
    ],
    'US': [
        'California', 'Texas', 'Florida', 'New York', 'Illinois', 'Pennsylvania', 'Ohio', 'Georgia', 'North Carolina', 'Michigan'
    ],
}

CATALOGOS_CIUDADES = {
    'CL': {
        'Región Metropolitana': ['Santiago', 'Puente Alto', 'Maipú'],
        'Valparaíso': ['Valparaíso', 'Viña del Mar', 'Quilpué'],
        # ...
    },
    'US': {
        'California': ['Los Angeles', 'San Francisco', 'San Diego'],
        'Texas': ['Houston', 'Dallas', 'Austin'],
        # ...
    },
}

CATALOGOS_SERVICIOS = {
    'CL': ['Mantención', 'Revisión técnica', 'Cambio de aceite', 'Frenos', 'Alineación'],
    'US': ['Oil Change', 'Brake Service', 'Tire Rotation', 'State Inspection', 'Battery Replacement'],
}

CATALOGOS_TIPOS_AUTO = {
    'CL': ['Sedán', 'Hatchback', 'SUV', 'Camioneta', 'Furgón'],
    'US': ['Sedan', 'SUV', 'Pickup Truck', 'Van', 'Convertible'],
}

def get_regiones(pais):
    return CATALOGOS_REGIONES.get(pais, [])

def get_ciudades(pais, region):
    return CATALOGOS_CIUDADES.get(pais, {}).get(region, [])

def get_servicios(pais):
    return CATALOGOS_SERVICIOS.get(pais, [])

def get_tipos_auto(pais):
    return CATALOGOS_TIPOS_AUTO.get(pais, [])

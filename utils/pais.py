"""
Utilidades centralizadas para catálogos, validaciones y configuración por país (Chile, USA, etc)
"""



import os
import json

CATALOGOS_CIUDADES = {
    'CL': {
        'Región de Arica y Parinacota': ['Arica', 'Camarones', 'General Lagos', 'Putre'],
        'Región de Tarapacá': ['Iquique', 'Alto Hospicio', 'Pozo Almonte', 'Camiña', 'Colchane', 'Huara', 'Pica'],
        'Región de Antofagasta': ['Antofagasta', 'Mejillones', 'Sierra Gorda', 'Taltal', 'Calama', 'Ollagüe', 'San Pedro de Atacama', 'Tocopilla', 'María Elena'],
        'Región de Atacama': ['Copiapó', 'Caldera', 'Tierra Amarilla', 'Chañaral', 'Diego de Almagro', 'Vallenar', 'Alto del Carmen', 'Freirina', 'Huasco'],
        'Región de Coquimbo': ['La Serena', 'Coquimbo', 'Andacollo', 'La Higuera', 'Paiguano', 'Vicuña', 'Illapel', 'Canela', 'Los Vilos', 'Salamanca', 'Ovalle', 'Combarbalá', 'Monte Patria', 'Punitaqui', 'Río Hurtado'],
        'Región de Valparaíso': ['Valparaíso', 'Casablanca', 'Concón', 'Juan Fernández', 'Puchuncaví', 'Quintero', 'Viña del Mar', 'Isla de Pascua', 'Los Andes', 'Calle Larga', 'Rinconada', 'San Esteban', 'La Ligua', 'Cabildo', 'Papudo', 'Petorca', 'Zapallar', 'Quillota', 'Calera', 'Hijuelas', 'La Cruz', 'Nogales', 'San Antonio', 'Algarrobo', 'Cartagena', 'El Quisco', 'El Tabo', 'San Antonio', 'Santo Domingo', 'San Felipe', 'Catemu', 'Llaillay', 'Panquehue', 'Putaendo', 'Santa María', 'Quilpué', 'Limache', 'Olmué', 'Villa Alemana'],
        'Región Metropolitana de Santiago': ['Cerrillos', 'Cerro Navia', 'Conchalí', 'El Bosque', 'Estación Central', 'Huechuraba', 'Independencia', 'La Cisterna', 'La Florida', 'La Granja', 'La Pintana', 'La Reina', 'Las Condes', 'Lo Barnechea', 'Lo Espejo', 'Lo Prado', 'Macul', 'Maipú', 'Ñuñoa', 'Pedro Aguirre Cerda', 'Peñalolén', 'Providencia', 'Pudahuel', 'Quilicura', 'Quinta Normal', 'Recoleta', 'Renca', 'San Joaquín', 'San Miguel', 'San Ramón', 'Vitacura', 'Puente Alto', 'Pirque', 'San José de Maipo', 'Colina', 'Lampa', 'Tiltil', 'San Bernardo', 'Buin', 'Calera de Tango', 'Paine', 'Melipilla', 'Alhué', 'Curacaví', 'María Pinto', 'San Pedro', 'Talagante', 'El Monte', 'Isla de Maipo', 'Padre Hurtado', 'Peñaflor'],
        'Región del Libertador General Bernardo O’Higgins': ['Rancagua', 'Codegua', 'Coinco', 'Coltauco', 'Doñihue', 'Graneros', 'Las Cabras', 'Machalí', 'Malloa', 'Mostazal', 'Olivar', 'Peumo', 'Pichidegua', 'Quinta de Tilcoco', 'Rengo', 'Requínoa', 'San Vicente', 'Pichilemu', 'La Estrella', 'Litueche', 'Marchihue', 'Navidad', 'Paredones', 'San Fernando', 'Chépica', 'Chimbarongo', 'Lolol', 'Nancagua', 'Palmilla', 'Peralillo', 'Placilla', 'Pumanque', 'Santa Cruz'],
        'Región del Maule': ['Talca', 'Constitución', 'Curepto', 'Empedrado', 'Maule', 'Pelarco', 'Pencahue', 'Río Claro', 'San Clemente', 'San Rafael', 'Cauquenes', 'Chanco', 'Pelluhue', 'Curicó', 'Hualañé', 'Licantén', 'Molina', 'Rauco', 'Romeral', 'Sagrada Familia', 'Teno', 'Vichuquén', 'Linares', 'Colbún', 'Longaví', 'Parral', 'Retiro', 'San Javier', 'Villa Alegre', 'Yerbas Buenas'],
        'Región de Ñuble': ['Chillán', 'Bulnes', 'Cobquecura', 'Coelemu', 'Coihueco', 'El Carmen', 'Ninhue', 'Ñiquén', 'Pemuco', 'Pinto', 'Portezuelo', 'Quillón', 'Quirihue', 'Ránquil', 'San Carlos', 'San Fabián', 'San Ignacio', 'San Nicolás', 'Treguaco', 'Yungay'],
        'Región del Biobío': ['Concepción', 'Coronel', 'Chiguayante', 'Florida', 'Hualpén', 'Hualqui', 'Lota', 'Penco', 'San Pedro de la Paz', 'Santa Juana', 'Talcahuano', 'Tomé', 'Tucapel', 'Yumbel', 'Cabrero', 'Laja', 'Los Ángeles', 'Mulchén', 'Nacimiento', 'Negrete', 'Quilaco', 'Quilleco', 'San Rosendo', 'Santa Bárbara', 'Tucapel', 'Alto Biobío', 'Antuco', 'Curanilahue', 'Arauco', 'Cañete', 'Contulmo', 'Lebu', 'Los Álamos', 'Tirúa'],
        'Región de La Araucanía': ['Temuco', 'Carahue', 'Cunco', 'Curarrehue', 'Freire', 'Galvarino', 'Gorbea', 'Lautaro', 'Loncoche', 'Melipeuco', 'Nueva Imperial', 'Padre Las Casas', 'Perquenco', 'Pitrufquén', 'Pucón', 'Saavedra', 'Teodoro Schmidt', 'Toltén', 'Vilcún', 'Villarrica', 'Cholchol', 'Angol', 'Collipulli', 'Curacautín', 'Ercilla', 'Lonquimay', 'Los Sauces', 'Lumaco', 'Purén', 'Renaico', 'Traiguén', 'Victoria'],
        'Región de Los Ríos': ['Valdivia', 'Corral', 'Lanco', 'Los Lagos', 'Máfil', 'Mariquina', 'Paillaco', 'Panguipulli', 'La Unión', 'Futrono', 'Lago Ranco', 'Río Bueno'],
        'Región de Los Lagos': ['Puerto Montt', 'Calbuco', 'Cochamó', 'Fresia', 'Frutillar', 'Llanquihue', 'Los Muermos', 'Maullín', 'Puerto Varas', 'Ancud', 'Castro', 'Chonchi', 'Curaco de Vélez', 'Dalcahue', 'Puqueldón', 'Queilén', 'Quellón', 'Quemchi', 'Quinchao', 'Osorno', 'Puerto Octay', 'Purranque', 'Río Negro', 'San Juan de la Costa', 'San Pablo', 'Chaitén', 'Futaleufú', 'Hualaihué', 'Palena'],
        'Región de Aysén del General Carlos Ibáñez del Campo': ['Coyhaique', 'Aysén', 'Cisnes', 'Guaitecas', 'Cochrane', 'O’Higgins', 'Tortel', 'Chile Chico', 'Río Ibáñez', 'Lago Verde'],
        'Región de Magallanes y de la Antártica Chilena': ['Punta Arenas', 'Puerto Natales', 'Porvenir', 'Cabo de Hornos', 'Laguna Blanca', 'Río Verde', 'San Gregorio', 'Timaukel', 'Primavera', 'Antártica'],
    },
    'US': None,  # Se cargará dinámicamente
}

 # Cargar estados y ciudades de USA desde el JSON externo
_json_path = os.path.join(os.path.dirname(__file__), 'estados_ciudades_usa.json')
try:
    with open(_json_path, encoding='utf-8') as f:
        data_us = json.load(f)
        if isinstance(data_us, dict) and data_us:
            CATALOGOS_CIUDADES['US'] = data_us
        else:
            print("Advertencia: El JSON de USA está vacío o malformado.")
            CATALOGOS_CIUDADES['US'] = {}
except Exception as e:
    print(f"Error cargando estados_ciudades_usa.json: {e}")
    CATALOGOS_CIUDADES['US'] = {}


# Definir CATALOGOS_REGIONES después de cargar el JSON de USA
def _ordenar_estados_us(ciudades_us):
    if not ciudades_us:
        return []
    estados = list(ciudades_us.keys())
    if 'Georgia' in estados:
        estados.remove('Georgia')
        return ['Georgia'] + sorted(estados)
    return sorted(estados)

CATALOGOS_REGIONES = {
    'CL': list(CATALOGOS_CIUDADES['CL'].keys()),
    'US': _ordenar_estados_us(CATALOGOS_CIUDADES['US']),
}

CATALOGOS_SERVICIOS = {
    'CL': ['Mantención', 'Revisión técnica', 'Cambio de aceite', 'Frenos', 'Alineación'],
    'US': ['Oil Change', 'Brake Service', 'Tire Rotation', 'State Inspection', 'Battery Replacement'],
}

CATALOGOS_TIPOS_AUTO = {
    'CL': ['Sedán', 'Hatchback', 'SUV', 'Camioneta', 'Furgón'],
    'US': ['Sedan', 'SUV', 'Pickup Truck', 'Van', 'Convertible'],
}

# --- Configuración y validaciones ---
def get_configuracion_pais(empresa):
    if empresa.pais == 'US':
        return {
            'moneda': 'USD',
            'simbolo_moneda': '$',
            'decimales': 2,
            'idioma_default': 'en',
            'formato_fecha': '%m/%d/%Y',
            'zona_horaria_default': 'America/New_York',
            'validacion_patente': r'^[A-Z0-9]{2,7}$',
            'impuesto_default': 0.08,
        }
    else:
        return {
            'moneda': 'CLP',
            'simbolo_moneda': '$',
            'decimales': 0,
            'idioma_default': 'es',
            'formato_fecha': '%d/%m/%Y',
            'zona_horaria_default': 'America/Santiago',
            'validacion_patente': r'^[A-Z]{2}\d{4}$',
            'impuesto_default': 0.19,
        }


def get_regiones(pais):
    regiones = CATALOGOS_REGIONES.get(pais)
    if regiones is None:
        return []
    return regiones


def get_ciudades(pais, region):
    ciudades_por_pais = CATALOGOS_CIUDADES.get(pais)
    if not ciudades_por_pais or not region:
        return []
    # DEBUG: Mostrar qué valor de region se recibe y las claves disponibles
    if pais == 'US':
        print(f"[DEBUG] region recibida: '{region}'")
        print(f"[DEBUG] claves disponibles: {list(ciudades_por_pais.keys())}")
        region_normalizada = region.strip()
        for key in ciudades_por_pais.keys():
            if key.strip().lower() == region_normalizada.lower():
                print(f"[DEBUG] Coincidencia encontrada: '{key}'")
                return ciudades_por_pais[key]
        print("[DEBUG] No se encontró coincidencia para la región seleccionada.")
        return []
    return ciudades_por_pais.get(region, [])

def get_servicios(pais):
    return CATALOGOS_SERVICIOS.get(pais, [])

def get_tipos_auto(pais):
    return CATALOGOS_TIPOS_AUTO.get(pais, [])

def formatear_precio(precio, empresa):
    config = get_configuracion_pais(empresa)
    if config['decimales'] > 0:
        return f"{config['simbolo_moneda']}{precio:.{config['decimales']}f} {config['moneda']}"
    else:
        return f"{config['simbolo_moneda']}{precio:,.0f} {config['moneda']}"

def validar_patente_por_pais(patente, pais):
    import re
    if pais == 'US':
        return bool(re.match(r'^[A-Z0-9]{2,8}$', patente.upper()))
    else:
        return bool(re.match(r'^[A-Z]{2,4}\d{2,4}$', patente.upper()))

def validar_telefono_por_pais(telefono, pais):
    import re
    if pais == 'US':
        patron = r'^(\+1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$'
        return bool(re.match(patron, telefono))
    else:
        patron = r'^(\+56)?[0-9]{8,9}$'
        return bool(re.match(patron, telefono.replace(' ', '').replace('-', '')))

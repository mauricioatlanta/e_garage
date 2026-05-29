# -*- coding: utf-8 -*-
"""
Traducciones de rubros de talleres por país.
Cada país tiene su propio slang y cultura para nombrar los tipos de talleres.
"""

# Traducciones por país (código ISO del país)
RUBROS_BY_COUNTRY = {
    # 🇺🇸 Estados Unidos - USA
    "US": {
        "WORKSHOP": "Full-Service Auto Shop",
        "WORKSHOP_MOTO": "Motorcycle Repair Shop",
        "WORKSHOP_HEAVY": "Truck & Bus Repair Shop",
        "EXHAUST": "Exhaust & Muffler Shop",
        "PARTS": "Auto Parts Store",
        "TIRE": "Tire Shop & Tire Service",
        "BODYSHOP": "Body Shop & Paint",
        "DETAILING": "Car Wash, Detailing & Aesthetics",
        "ELECTRIC": "Automotive Electrical & Electronics",
        "GLASS_AUDIO": "Windshield, Glass & Audio / Accessories",
        "FLEET": "Fleet Maintenance",
        "SUSPENSION_STEERING": "Suspension & Steering Shop",
        "BRAKES": "Brake Shop",
        "OBD_DIAGNOSTIC": "Computerized Diagnostic Shop (OBD-II)",
        "CLASSIC_CARS": "Classic Car Restoration Shop",
        "AUDIO_ENTERTAINMENT": "Car Audio & Entertainment Systems",
        "GAS_CONVERSION": "Gas Conversion Shop (LPG/CNG)",
        "FLEET_REPAIR": "Corporate Fleet Repair Shop",
        "BODY_GLASS": "Body & Glass Repair Shop",
        "TUNING": "Tuning & Customization Shop",
        "MIXED": "Mixed Services (Multiple Industries)",
    },
    # 🇨🇱 Chile
    "CL": {
        "WORKSHOP": "Taller mecánico integral",
        "WORKSHOP_MOTO": "Taller de motos",
        "WORKSHOP_HEAVY": "Taller de camiones/buses",
        "EXHAUST": "Taller de escapes y mufflers",
        "PARTS": "Casa de repuestos / Autopartes",
        "TIRE": "Vulcanización / Neumáticos y llantas",
        "BODYSHOP": "Carrocería / Pintura",
        "DETAILING": "Lavado, detailing y estética",
        "ELECTRIC": "Electricidad / Electrónica automotriz",
        "GLASS_AUDIO": "Parabrisas, vidrios y audio / accesorios",
        "FLEET": "Mantención de flotas empresariales",
        "SUSPENSION_STEERING": "Taller de Suspensión y Dirección",
        "BRAKES": "Taller de Frenos",
        "OBD_DIAGNOSTIC": "Taller de Diagnóstico Computarizado (OBD-II)",
        "CLASSIC_CARS": "Taller de Reparación de Vehículos Clásicos",
        "AUDIO_ENTERTAINMENT": "Taller de Sistemas de Audio y Entretenimiento Automotriz",
        "GAS_CONVERSION": "Taller de Conversiones a Gas",
        "FLEET_REPAIR": "Taller de Reparación de Flotas Corporativas",
        "BODY_GLASS": "Taller de Carrocería y Reparación de Vidrios",
        "TUNING": "Taller de Tuning / Personalización",
        "MIXED": "Mixto (varios rubros)",
    },
    # 🇲🇽 México
    "MX": {
        "WORKSHOP": "Taller mecánico integral",
        "WORKSHOP_MOTO": "Taller de motos",
        "WORKSHOP_HEAVY": "Taller de camiones/autobuses",
        "EXHAUST": "Taller de escapes y silenciadores",
        "PARTS": "Casa de refacciones / Autopartes",
        "TIRE": "Vulcanización / Llantas y neumáticos",
        "BODYSHOP": "Hojalatería / Pintura",
        "DETAILING": "Lavado, detailing y estética",
        "ELECTRIC": "Electricidad / Electrónica automotriz",
        "GLASS_AUDIO": "Parabrisas, vidrios y audio / accesorios",
        "FLEET": "Mantenimiento de flotas empresariales",
        "SUSPENSION_STEERING": "Taller de Suspensión y Dirección",
        "BRAKES": "Taller de Frenos",
        "OBD_DIAGNOSTIC": "Taller de Diagnóstico Computarizado (OBD-II)",
        "CLASSIC_CARS": "Taller de Restauración de Autos Clásicos",
        "AUDIO_ENTERTAINMENT": "Taller de Sistemas de Audio y Entretenimiento Automotriz",
        "GAS_CONVERSION": "Taller de Conversiones a Gas",
        "FLEET_REPAIR": "Taller de Reparación de Flotas Corporativas",
        "BODY_GLASS": "Taller de Hojalatería y Reparación de Vidrios",
        "TUNING": "Taller de Tuning / Personalización",
        "MIXED": "Mixto (varios servicios)",
    },
    # 🇵🇪 Perú
    "PE": {
        "WORKSHOP": "Taller mecánico integral",
        "WORKSHOP_MOTO": "Taller de motos",
        "WORKSHOP_HEAVY": "Taller de camiones/buses",
        "EXHAUST": "Taller de escapes y silenciadores",
        "PARTS": "Casa de repuestos / Autopartes",
        "TIRE": "Vulcanización / Llantas y neumáticos",
        "BODYSHOP": "Carrocería / Pintura",
        "DETAILING": "Lavado, detailing y estética",
        "ELECTRIC": "Electricidad / Electrónica automotriz",
        "GLASS_AUDIO": "Parabrisas, vidrios y audio / accesorios",
        "FLEET": "Mantenimiento de flotas empresariales",
        "SUSPENSION_STEERING": "Taller de Suspensión y Dirección",
        "BRAKES": "Taller de Frenos",
        "OBD_DIAGNOSTIC": "Taller de Diagnóstico Computarizado (OBD-II)",
        "CLASSIC_CARS": "Taller de Restauración de Vehículos Clásicos",
        "AUDIO_ENTERTAINMENT": "Taller de Sistemas de Audio y Entretenimiento Automotriz",
        "GAS_CONVERSION": "Taller de Conversiones a Gas",
        "FLEET_REPAIR": "Taller de Reparación de Flotas Corporativas",
        "BODY_GLASS": "Taller de Carrocería y Reparación de Vidrios",
        "TUNING": "Taller de Tuning / Personalización",
        "MIXED": "Mixto (varios rubros)",
    },
    # 🇻🇪 Venezuela
    "VE": {
        "WORKSHOP": "Taller mecánico integral",
        "WORKSHOP_MOTO": "Taller de motos",
        "WORKSHOP_HEAVY": "Taller de camiones/buses",
        "EXHAUST": "Taller de escapes y silenciadores",
        "PARTS": "Casa de repuestos / Autopartes",
        "TIRE": "Vulcanización / Cauchos y rines",
        "BODYSHOP": "Hojalatería / Pintura",
        "DETAILING": "Lavado, detailing y estética",
        "ELECTRIC": "Electricidad / Electrónica automotriz",
        "GLASS_AUDIO": "Parabrisas, vidrios y audio / accesorios",
        "FLEET": "Mantenimiento de flotas empresariales",
        "SUSPENSION_STEERING": "Taller de Suspensión y Dirección",
        "BRAKES": "Taller de Frenos",
        "OBD_DIAGNOSTIC": "Taller de Diagnóstico Computarizado (OBD-II)",
        "CLASSIC_CARS": "Taller de Restauración de Vehículos Clásicos",
        "AUDIO_ENTERTAINMENT": "Taller de Sistemas de Audio y Entretenimiento Automotriz",
        "GAS_CONVERSION": "Taller de Conversiones a Gas",
        "FLEET_REPAIR": "Taller de Reparación de Flotas Corporativas",
        "BODY_GLASS": "Taller de Hojalatería y Reparación de Vidrios",
        "TUNING": "Taller de Tuning / Personalización",
        "MIXED": "Mixto (varios servicios)",
    },
    # 🇧🇷 Brasil
    "BR": {
        "WORKSHOP": "Oficina mecânica completa",
        "WORKSHOP_MOTO": "Oficina de motos",
        "WORKSHOP_HEAVY": "Oficina de caminhões/ônibus",
        "EXHAUST": "Oficina de escapamentos e silenciadores",
        "PARTS": "Loja de peças / Autopeças",
        "TIRE": "Vulcanização / Pneus e rodas",
        "BODYSHOP": "Funilaria / Pintura",
        "DETAILING": "Lavagem, detailing e estética",
        "ELECTRIC": "Elétrica / Eletrônica automotiva",
        "GLASS_AUDIO": "Para-brisas, vidros e áudio / Acessórios",
        "FLEET": "Manutenção de frotas empresariais",
        "SUSPENSION_STEERING": "Oficina de Suspensão e Direção",
        "BRAKES": "Oficina de Freios",
        "OBD_DIAGNOSTIC": "Oficina de Diagnóstico Computadorizado (OBD-II)",
        "CLASSIC_CARS": "Oficina de Restauração de Carros Clássicos",
        "AUDIO_ENTERTAINMENT": "Oficina de Sistemas de Áudio e Entretenimento Automotivo",
        "GAS_CONVERSION": "Oficina de Conversões para Gás",
        "FLEET_REPAIR": "Oficina de Reparação de Frotas Corporativas",
        "BODY_GLASS": "Oficina de Funilaria e Reparação de Vidros",
        "TUNING": "Oficina de Tuning / Personalização",
        "MIXED": "Misto (vários serviços)",
    },
    # 🇨🇴 Colombia (por si acaso)
    "CO": {
        "WORKSHOP": "Taller mecánico integral",
        "WORKSHOP_MOTO": "Taller de motos",
        "WORKSHOP_HEAVY": "Taller de camiones/buses",
        "EXHAUST": "Taller de escapes y silenciadores",
        "PARTS": "Casa de repuestos / Autopartes",
        "TIRE": "Vulcanización / Llantas y neumáticos",
        "BODYSHOP": "Hojalatería / Pintura",
        "DETAILING": "Lavado, detailing y estética",
        "ELECTRIC": "Electricidad / Electrónica automotriz",
        "GLASS_AUDIO": "Parabrisas, vidrios y audio / accesorios",
        "FLEET": "Mantenimiento de flotas empresariales",
        "SUSPENSION_STEERING": "Taller de Suspensión y Dirección",
        "BRAKES": "Taller de Frenos",
        "OBD_DIAGNOSTIC": "Taller de Diagnóstico Computarizado (OBD-II)",
        "CLASSIC_CARS": "Taller de Restauración de Vehículos Clásicos",
        "AUDIO_ENTERTAINMENT": "Taller de Sistemas de Audio y Entretenimiento Automotriz",
        "GAS_CONVERSION": "Taller de Conversiones a Gas",
        "FLEET_REPAIR": "Taller de Reparación de Flotas Corporativas",
        "BODY_GLASS": "Taller de Hojalatería y Reparación de Vidrios",
        "TUNING": "Taller de Tuning / Personalización",
        "MIXED": "Mixto (varios servicios)",
    },
}


def get_rubros_translated(country_code="CL"):
    """
    Retorna las traducciones de rubros para un país específico.

    Args:
        country_code: Código ISO del país (US, CL, MX, PE, VE, BR, CO)

    Returns:
        dict: Diccionario con las traducciones {codigo: nombre_traducido}
    """
    country_code = str(country_code).upper().strip()
    return RUBROS_BY_COUNTRY.get(country_code, RUBROS_BY_COUNTRY["CL"])


def get_rubro_label(rubro_code, country_code="CL"):
    """
    Obtiene la etiqueta traducida de un rubro específico para un país.

    Args:
        rubro_code: Código del rubro (ej: "WORKSHOP")
        country_code: Código ISO del país (US, CL, MX, PE, VE, BR, CO)

    Returns:
        str: Etiqueta traducida o el código si no se encuentra
    """
    translations = get_rubros_translated(country_code)
    return translations.get(rubro_code, rubro_code)


def get_rubros_choices_for_country(country_code="CL"):
    """
    Retorna las opciones de rubros traducidas para un país específico.

    Args:
        country_code: Código ISO del país (US, CL, MX, PE, VE, BR, CO)

    Returns:
        list: Lista de tuplas (codigo, nombre_traducido)
    """
    from taller.config.rubros import RUBROS_TALLER

    translations = get_rubros_translated(country_code)
    return [(code, translations.get(code, label)) for code, label in RUBROS_TALLER]

#!/usr/bin/env python3
"""
Script simplificado para cargar el Catálogo Maestro Universal de Servicios

Este script es una versión simplificada y directa para poblar rápidamente
el catálogo maestro con servicios globales (empresa_id=1).

Uso:
    python manage.py shell
    >>> exec(open('scripts/cargar_catalogo_maestro_simple.py').read())
    >>> poblar_catalogo_maestro()
"""

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from decimal import Decimal
from taller.models.empresa import Empresa
from taller.servicios.models import (
    Servicio,
    CategoriaServicio,
    CategoriaServicioName,
    ServicioName,
    SubcategoriaServicio,
    SubcategoriaServicioName,
)


def poblar_catalogo_maestro(country="US"):
    """
    Pobla el catálogo maestro con servicios globales.

    Args:
        country: Código de país ("US", "CL", "MX", etc.)

    Returns:
        str: Mensaje de confirmación
    """
    # ID de la empresa maestra (Global)
    MASTER_ID = 1

    # Obtener o crear empresa maestra
    try:
        empresa_maestra = Empresa.objects.get(id=MASTER_ID)
    except Empresa.DoesNotExist:
        from django.contrib.auth.models import User

        # Crear usuario sistema si no existe
        user_sistema, _ = User.objects.get_or_create(
            username="sistema_catalogo_maestro",
            defaults={
                "email": "sistema@egarage.com",
                "is_active": False,
            },
        )

        # Crear empresa maestra
        empresa_maestra = Empresa.objects.create(
            id=MASTER_ID,
            user=user_sistema,
            nombre_taller="Catálogo Maestro Global",
            empresa="Sistema eGarage",
            pais=country,
            is_trial=False,
        )
        print(f"✅ Empresa maestra creada: {empresa_maestra.nombre_taller}")

    # Mapeo de idioma por país
    language_map = {
        "US": "en",
        "CL": "es",
        "MX": "es",
        "PE": "es",
        "VE": "es",
        "BR": "pt",
    }
    language = language_map.get(country, "es")

    # Definición del catálogo
    catalogo = {
        "mantenimiento": {
            "label_es": "Mantenimiento Periódico",
            "label_en": "Preventive Maintenance & Periodic Services",
            "label_pt": "Manutenção Periódica",
            "aliases_es": ["mantenimiento", "preventivo", "servicio periódico"],
            "aliases_en": ["maintenance", "preventive", "periodic service"],
            "aliases_pt": ["manutenção", "preventivo", "serviço periódico"],
            "servicios": [
                {
                    "nombre_es": "Cambio de aceite sintético completo",
                    "nombre_en": "Full Synthetic Oil Change",
                    "nombre_pt": "Troca de óleo sintético completo",
                    "aliases": [
                        "aceite sintético",
                        "lube",
                        "oil filter",
                        "sintético",
                        "full synthetic",
                    ],
                },
                {
                    "nombre_es": "Cambio de aceite convencional",
                    "nombre_en": "Conventional Oil Change",
                    "nombre_pt": "Troca de óleo convencional",
                    "aliases": ["aceite mineral", "cambio aceite", "conventional", "mineral"],
                },
                {
                    "nombre_es": "Rotación de neumáticos y revisión de presión",
                    "nombre_en": "Tire Rotation & Pressure Check",
                    "nombre_pt": "Rotação de pneus e verificação de pressão",
                    "aliases": [
                        "rotación",
                        "aire neumáticos",
                        "tire rotation",
                        "pressure check",
                        "rotação",
                    ],
                },
                {
                    "nombre_es": "Cambio de filtro de aire del motor",
                    "nombre_en": "Engine Air Filter Replacement",
                    "nombre_pt": "Troca de filtro de ar do motor",
                    "aliases": ["filtro aire", "air filter", "filtro motor", "engine filter"],
                },
                {
                    "nombre_es": "Cambio de filtro de cabina",
                    "nombre_en": "Cabin Air Filter Replacement",
                    "nombre_pt": "Troca de filtro de cabine",
                    "aliases": [
                        "filtro polen",
                        "aire acondicionado",
                        "cabin filter",
                        "pollen filter",
                    ],
                },
                {
                    "nombre_es": "Cambio de bujías",
                    "nombre_en": "Spark Plugs Replacement",
                    "nombre_pt": "Troca de velas",
                    "aliases": ["bujías", "tune up", "spark plugs", "velas", "ignição"],
                },
                {
                    "nombre_es": "Limpieza de inyectores (presurizada)",
                    "nombre_en": "Fuel Injector Cleaning (Pressurized)",
                    "nombre_pt": "Limpeza de injetores (pressurizada)",
                    "aliases": [
                        "limpieza inyectores",
                        "fuel injector",
                        "injetores",
                        "limpeza injetores",
                    ],
                },
            ],
        },
        "frenos": {
            "label_es": "Sistema de Frenos",
            "label_en": "Braking System",
            "label_pt": "Sistema de Freios",
            "aliases_es": ["frenos", "frenado", "pastillas"],
            "aliases_en": ["brakes", "braking", "pads"],
            "aliases_pt": ["freios", "freagem", "pastilhas"],
            "servicios": [
                {
                    "nombre_es": "Cambio de pastillas de freno delanteras",
                    "nombre_en": "Front Brake Pads Replacement",
                    "nombre_pt": "Troca de pastilhas dianteiras",
                    "aliases": [
                        "pastillas delanteras",
                        "frenos",
                        "front pads",
                        "pastilhas dianteiras",
                    ],
                },
                {
                    "nombre_es": "Cambio de pastillas de freno traseras",
                    "nombre_en": "Rear Brake Pads Replacement",
                    "nombre_pt": "Troca de pastilhas traseiras",
                    "aliases": ["pastillas traseras", "rear pads", "pastilhas traseiras"],
                },
                {
                    "nombre_es": "Rectificado de discos de freno",
                    "nombre_en": "Brake Rotor Resurfacing",
                    "nombre_pt": "Retificação de discos de freio",
                    "aliases": ["rectificado discos", "rotor resurfacing", "retificação discos"],
                },
                {
                    "nombre_es": "Purga y cambio de líquido de frenos",
                    "nombre_en": "Brake Fluid Flush & Replace",
                    "nombre_pt": "Purga e troca de fluido de freios",
                    "aliases": ["líquido frenos", "brake fluid", "fluido freios", "purga"],
                },
                {
                    "nombre_es": "Cambio de cilindro maestro de frenos",
                    "nombre_en": "Brake Master Cylinder Replacement",
                    "nombre_pt": "Troca de cilindro mestre de freios",
                    "aliases": ["bomba de freno", "master cylinder", "cilindro mestre"],
                },
            ],
        },
        "motor_transmision": {
            "label_es": "Motor y Transmisión",
            "label_en": "Engine & Transmission",
            "label_pt": "Motor e Transmissão",
            "aliases_es": ["motor", "transmisión", "caja"],
            "aliases_en": ["engine", "transmission", "gearbox"],
            "aliases_pt": ["motor", "transmissão", "câmbio"],
            "servicios": [
                {
                    "nombre_es": "Cambio de correa/cadena de distribución",
                    "nombre_en": "Timing Belt / Chain Replacement",
                    "nombre_pt": "Troca de correia/corrente de distribuição",
                    "aliases": [
                        "correa distribución",
                        "faja",
                        "timing belt",
                        "timing chain",
                        "distribuição",
                    ],
                },
                {
                    "nombre_es": "Cambio de kit de embrague",
                    "nombre_en": "Clutch Kit Replacement",
                    "nombre_pt": "Troca de kit de embreagem",
                    "aliases": ["embrague", "cloche", "clutch", "embreagem"],
                },
                {
                    "nombre_es": "Servicio de fluido de transmisión",
                    "nombre_en": "Transmission Fluid Service",
                    "nombre_pt": "Serviço de fluido de transmissão",
                    "aliases": [
                        "aceite caja",
                        "transmisión",
                        "atf",
                        "transmissão",
                        "fluido câmbio",
                    ],
                },
                {
                    "nombre_es": "Cambio de bomba de agua",
                    "nombre_en": "Water Pump Replacement",
                    "nombre_pt": "Troca de bomba d'água",
                    "aliases": ["bomba de agua", "water pump", "bomba água", "bomba refrigerante"],
                },
                {
                    "nombre_es": "Cambio de junta de tapa de válvulas",
                    "nombre_en": "Valve Cover Gasket Replacement",
                    "nombre_pt": "Troca de junta de tampa de válvulas",
                    "aliases": [
                        "empaquetadura tapa válvulas",
                        "valve cover gasket",
                        "junta válvulas",
                    ],
                },
            ],
        },
        "rectificacion": {
            "label_es": "Rectificación de Motores",
            "label_en": "Machine Shop (Rectificación)",
            "label_pt": "Retificação de Motores",
            "aliases_es": ["rectificación", "machine shop", "encamisado"],
            "aliases_en": ["machining", "machine shop", "boring"],
            "aliases_pt": ["retificação", "usinagem", "encamisamento"],
            "servicios": [
                {
                    "nombre_es": "Rectificado de culata",
                    "nombre_en": "Cylinder Head Resurfacing",
                    "nombre_pt": "Retificação de cabeçote",
                    "aliases": [
                        "rectificado culata",
                        "cepillado",
                        "head resurfacing",
                        "retificação cabeçote",
                    ],
                },
                {
                    "nombre_es": "Reparación de válvulas y rectificado de asientos",
                    "nombre_en": "Valve Job & Seat Grinding",
                    "nombre_pt": "Reparo de válvulas e retificação de assentos",
                    "aliases": ["asiento válvulas", "rectificado", "valve job", "válvulas"],
                },
                {
                    "nombre_es": "Perforado y honeado de cilindros",
                    "nombre_en": "Cylinder Boring & Honing",
                    "nombre_pt": "Furação e alesamento de cilindros",
                    "aliases": ["encamisado", "perforado", "boring", "honing", "encamisamento"],
                },
                {
                    "nombre_es": "Rectificado de volante",
                    "nombre_en": "Flywheel Resurfacing",
                    "nombre_pt": "Retificação de volante",
                    "aliases": ["rectificado volante", "flywheel", "retificação volante"],
                },
                {
                    "nombre_es": "Prueba de presión de bloque de motor",
                    "nombre_en": "Engine Block Pressure Test",
                    "nombre_pt": "Teste de pressão do bloco do motor",
                    "aliases": ["prueba de presión", "fisuras", "pressure test", "teste pressão"],
                },
            ],
        },
        "estetica": {
            "label_es": "Carwash y Detailing",
            "label_en": "Carwash & Detailing",
            "label_pt": "Lavagem e Detalhamento",
            "aliases_es": ["detailing", "carwash", "lavado", "pulido"],
            "aliases_en": ["detailing", "carwash", "wash", "polish"],
            "aliases_pt": ["detalhamento", "lavagem", "polimento"],
            "servicios": [
                {
                    "nombre_es": "Detallado completo interior y exterior",
                    "nombre_en": "Full Interior & Exterior Detail",
                    "nombre_pt": "Detalhamento completo interior e exterior",
                    "aliases": [
                        "lavado completo",
                        "detallado",
                        "full detail",
                        "detalhamento completo",
                    ],
                },
                {
                    "nombre_es": "Corrección de pintura y pulido de alto brillo",
                    "nombre_en": "Paint Correction & High-Gloss Polish",
                    "nombre_pt": "Correção de pintura e polimento de alto brilho",
                    "aliases": ["pulido", "brillo", "encerado", "polish", "wax", "polimento"],
                },
                {
                    "nombre_es": "Protección con sellado cerámico",
                    "nombre_en": "Ceramic Coating Protection",
                    "nombre_pt": "Proteção com revestimento cerâmico",
                    "aliases": ["sellado cerámico", "coating", "ceramic", "revestimento cerâmico"],
                },
                {
                    "nombre_es": "Limpieza profunda de tapicería",
                    "nombre_en": "Upholstery Deep Cleaning",
                    "nombre_pt": "Limpeza profunda de estofados",
                    "aliases": ["limpieza tapiz", "aspirado", "upholstery", "limpeza estofados"],
                },
                {
                    "nombre_es": "Limpieza detallada de compartimento motor",
                    "nombre_en": "Engine Bay Detailed Cleaning",
                    "nombre_pt": "Limpeza detalhada do compartimento do motor",
                    "aliases": ["lavado motor", "engine bay", "limpeza motor"],
                },
                {
                    "nombre_es": "Restauración de faros",
                    "nombre_en": "Headlight Restoration",
                    "nombre_pt": "Restauração de faróis",
                    "aliases": ["pulido focos", "headlight", "restauração faróis"],
                },
            ],
        },
        "bodyshop": {
            "label_es": "Desabolladura y Pintura",
            "label_en": "Bodywork & Paint",
            "label_pt": "Funilaria e Pintura",
            "aliases_es": ["pintura", "desabollado", "bodyshop", "chapa"],
            "aliases_en": ["paint", "bodywork", "bodyshop", "collision"],
            "aliases_pt": ["pintura", "funilaria", "bodyshop", "chapa"],
            "servicios": [
                {
                    "nombre_es": "Pintura completa de panel",
                    "nombre_en": "Full Panel Painting",
                    "nombre_pt": "Pintura completa de painel",
                    "aliases": ["pintura pieza", "barniz", "panel paint", "pintura painel"],
                },
                {
                    "nombre_es": "Reparación de abolladuras (PDR)",
                    "nombre_en": "Dent Repair (PDR)",
                    "nombre_pt": "Reparo de amassados (PDR)",
                    "aliases": ["desabollado", "sacar golpes", "dent repair", "funilaria"],
                },
                {
                    "nombre_es": "Reparación y retoque de parachoques",
                    "nombre_en": "Bumper Repair & Refinish",
                    "nombre_pt": "Reparo e retoque de para-choques",
                    "aliases": ["parachoques", "retoque", "bumper", "para-choques"],
                },
                {
                    "nombre_es": "Alineación de chasis",
                    "nombre_en": "Chassis Alignment",
                    "nombre_pt": "Alinhamento de chassi",
                    "aliases": [
                        "cuadratura chasis",
                        "estirado",
                        "chassis alignment",
                        "alinhamento chassi",
                    ],
                },
            ],
        },
        "especialidades": {
            "label_es": "Servicios Especializados",
            "label_en": "Specialized Services",
            "label_pt": "Serviços Especializados",
            "aliases_es": ["especializado", "rectificación", "escape", "vidrios"],
            "aliases_en": ["specialized", "machine shop", "exhaust", "glass"],
            "aliases_pt": ["especializado", "retificação", "escapamento", "vidros"],
            "servicios": [
                {
                    "nombre_es": "Alineación de ruedas (4 ruedas)",
                    "nombre_en": "Wheel Alignment (4-Wheel)",
                    "nombre_pt": "Alinhamento de rodas (4 rodas)",
                    "aliases": ["alineación", "wheel alignment", "alinhamento"],
                },
                {
                    "nombre_es": "Recarga de sistema A/C (R134a)",
                    "nombre_en": "A/C System Recharge (R134a)",
                    "nombre_pt": "Recarga de sistema de ar condicionado (R134a)",
                    "aliases": ["carga gas", "aire acondicionado", "ac recharge", "recarga ar"],
                },
                {
                    "nombre_es": "Reparación de silenciador y escape",
                    "nombre_en": "Muffler & Exhaust Repair",
                    "nombre_pt": "Reparo de silenciador e escapamento",
                    "aliases": ["escape", "silenciador", "soldadura", "exhaust", "muffler"],
                },
                {
                    "nombre_es": "Escaneo diagnóstico computarizado",
                    "nombre_en": "Computerized Diagnostic Scan",
                    "nombre_pt": "Varredura diagnóstica computadorizada",
                    "aliases": ["scanner", "check engine", "obd", "diagnóstico", "scanner"],
                },
                {
                    "nombre_es": "Prueba de batería y sistema de carga",
                    "nombre_en": "Battery & Charging System Test",
                    "nombre_pt": "Teste de bateria e sistema de carga",
                    "aliases": ["batería", "alternador", "battery", "charging", "bateria"],
                },
            ],
        },
    }

    servicios_creados = 0
    servicios_actualizados = 0

    for cat_code, info in catalogo.items():
        # Crear o obtener categoría
        categoria, created = CategoriaServicio.objects.get_or_create(
            code=cat_code, country=country, defaults={"activo": True}
        )

        if created:
            print(f"✅ Categoría creada: {cat_code}")

        # Crear nombres de categoría en todos los idiomas
        for lang in ["es", "en", "pt"]:
            label_key = f"label_{lang}"
            aliases_key = f"aliases_{lang}"

            if label_key in info:
                CategoriaServicioName.objects.update_or_create(
                    categoria=categoria,
                    language=lang,
                    is_default=True,
                    defaults={
                        "label": info[label_key],
                        "aliases": info.get(aliases_key, []),
                    },
                )

        # Crear servicios
        for s_data in info["servicios"]:
            # Obtener nombre según idioma del país
            nombre = s_data.get(f"nombre_{language}", s_data.get("nombre_en", ""))
            if not nombre:
                continue

            servicio, created = Servicio.objects.get_or_create(
                nombre=nombre,
                empresa_id=MASTER_ID,
                categoria=categoria,
                defaults={
                    "activo": True,
                    "precio_base": Decimal("0.00"),  # El usuario pondrá su precio
                },
            )

            if created:
                servicios_creados += 1
            else:
                servicios_actualizados += 1

            # Crear nombres localizados en todos los idiomas
            for lang in ["es", "en", "pt"]:
                nombre_key = f"nombre_{lang}"
                if nombre_key in s_data:
                    ServicioName.objects.update_or_create(
                        servicio=servicio,
                        language=lang,
                        is_default=(lang == language),
                        defaults={
                            "label": s_data[nombre_key],
                            "aliases": s_data.get("aliases", []),
                        },
                    )

            print(f"   🔧 {nombre}")

    total = Servicio.objects.filter(empresa_id=MASTER_ID).count()

    return f"""
✅ Catálogo maestro poblado exitosamente.
📊 Resumen:
   - Servicios creados: {servicios_creados}
   - Servicios actualizados: {servicios_actualizados}
   - Total en catálogo: {total}
   - País: {country}
   - Idioma principal: {language}
"""


# Ejecución directa
if __name__ == "__main__":
    # Poblar para múltiples países
    for country in ["US", "CL", "MX", "PE", "VE", "BR"]:
        print(f"\n{'='*60}")
        print(f"🌍 Poblando catálogo para país: {country}")
        print(f"{'='*60}")
        resultado = poblar_catalogo_maestro(country=country)
        print(resultado)

    print("\n" + "=" * 60)
    print("🎉 ¡Proceso completado!")
    print("=" * 60)

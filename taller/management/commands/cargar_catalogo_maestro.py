"""
Management command para cargar el Catálogo Maestro Universal desde JSON

Uso:
    python manage.py cargar_catalogo_maestro
    python manage.py cargar_catalogo_maestro --json scripts/catalogo_maestro_servicios.json
"""

from decimal import Decimal
import json
import os

from django.core.management.base import BaseCommand
from django.conf import settings

from taller.models.empresa import Empresa
from taller.servicios.models import (
    Servicio,
    CategoriaServicio,
    CategoriaServicioName,
    ServicioName,
)


class Command(BaseCommand):
    help = "Carga el catálogo maestro universal desde un archivo JSON"

    def add_arguments(self, parser):
        parser.add_argument(
            "--json",
            type=str,
            default="scripts/catalogo_maestro_servicios.json",
            help="Ruta al archivo JSON con los servicios maestros",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simula la carga sin guardar en la base de datos",
        )

    def handle(self, *args, **options):
        json_path = options["json"]
        dry_run = options["dry_run"]

        if dry_run:
            self.stdout.write(self.style.WARNING("[DRY-RUN] MODO DRY-RUN: No se guardarán cambios"))

        MASTER_ID = 1

        # Obtener o crear empresa maestra
        try:
            empresa_maestra = Empresa.objects.get(id=MASTER_ID)
            self.stdout.write(f"[OK] Empresa maestra encontrada: {empresa_maestra.nombre_taller}")
        except Empresa.DoesNotExist:
            if dry_run:
                self.stdout.write("[DRY-RUN] Se crearía empresa maestra")
            else:
                from django.contrib.auth.models import User
                user_sistema, _ = User.objects.get_or_create(
                    username="sistema_catalogo_maestro",
                    defaults={"email": "sistema@egarage.com", "is_active": False}
                )
                empresa_maestra = Empresa.objects.create(
                    id=MASTER_ID,
                    user=user_sistema,
                    nombre_taller="Catálogo Maestro Global",
                    empresa="Sistema eGarage",
                    pais="CL",
                )
                self.stdout.write(self.style.SUCCESS(f"[OK] Empresa maestra creada: {empresa_maestra.nombre_taller}"))

        # Configuración de países e idiomas
        paises_config = {
            "US": "en",
            "BR": "pt",
            "CL": "es",
            "MX": "es",
            "VE": "es",
            "PE": "es",
            "CO": "es",
            "EC": "es",
            "AR": "es",
            "UY": "es",
        }

        # Mapeo de categorías por país
        categorias_config = {
            "mantenimiento": {
                "CL": {"label": "Mantenimiento Periódico", "aliases": ["mantenimiento", "preventivo", "servicio periódico"]},
                "MX": {"label": "Mantenimiento Periódico", "aliases": ["mantenimiento", "preventivo", "servicio periódico"]},
                "AR": {"label": "Mantenimiento Periódico", "aliases": ["mantenimiento", "preventivo", "service"]},
                "UY": {"label": "Mantenimiento Periódico", "aliases": ["mantenimiento", "preventivo"]},
                "CO": {"label": "Mantenimiento Periódico", "aliases": ["mantenimiento", "preventivo"]},
                "EC": {"label": "Mantenimiento Periódico", "aliases": ["mantenimiento", "preventivo"]},
                "PE": {"label": "Mantenimiento Periódico", "aliases": ["mantenimiento", "preventivo"]},
                "VE": {"label": "Mantenimiento Periódico", "aliases": ["mantenimiento", "preventivo"]},
                "US": {"label": "Preventive Maintenance", "aliases": ["maintenance", "preventive", "periodic service"]},
                "BR": {"label": "Manutenção Periódica", "aliases": ["manutenção", "preventivo", "serviço periódico"]},
            },
            "bodyshop": {
                "CL": {"label": "Desabolladura y Pintura", "aliases": ["pintura", "desabollado", "bodyshop", "chapa"]},
                "MX": {"label": "Desabolladura y Pintura", "aliases": ["pintura", "desabollado", "bodyshop", "chapa"]},
                "AR": {"label": "Chapa y Pintura", "aliases": ["chapista", "choque", "bollo", "pintura"]},
                "UY": {"label": "Chapa y Pintura", "aliases": ["chapeado", "golpe", "pintura"]},
                "CO": {"label": "Latonería y Pintura", "aliases": ["golpe", "latas", "pintar", "latonería"]},
                "EC": {"label": "Enderezada y Pintura", "aliases": ["choque", "enderezado", "pintura"]},
                "PE": {"label": "Desabolladura y Pintura", "aliases": ["pintura", "desabollado", "chapa"]},
                "VE": {"label": "Desabolladura y Pintura", "aliases": ["pintura", "desabollado", "chapa"]},
                "US": {"label": "Bodywork & Paint", "aliases": ["paint", "bodywork", "bodyshop", "collision"]},
                "BR": {"label": "Funilaria e Pintura", "aliases": ["pintura", "funilaria", "bodyshop", "chapa"]},
            },
            "motor": {
                "CL": {"label": "Motor y Transmisión", "aliases": ["motor", "transmisión", "caja"]},
                "MX": {"label": "Motor y Transmisión", "aliases": ["motor", "transmisión", "caja"]},
                "AR": {"label": "Motor y Transmisión", "aliases": ["motor", "transmisión", "caja"]},
                "UY": {"label": "Motor y Transmisión", "aliases": ["motor", "transmisión", "caja"]},
                "CO": {"label": "Motor y Transmisión", "aliases": ["motor", "transmisión", "caja"]},
                "EC": {"label": "Motor y Transmisión", "aliases": ["motor", "transmisión", "caja"]},
                "PE": {"label": "Motor y Transmisión", "aliases": ["motor", "transmisión", "caja"]},
                "VE": {"label": "Motor y Transmisión", "aliases": ["motor", "transmisión", "caja"]},
                "US": {"label": "Engine & Transmission", "aliases": ["engine", "transmission", "gearbox"]},
                "BR": {"label": "Motor e Transmissão", "aliases": ["motor", "transmissão", "câmbio"]},
            },
            "especialidades": {
                "CL": {"label": "Servicios Especializados", "aliases": ["especializado", "servicios varios"]},
                "MX": {"label": "Servicios Especializados", "aliases": ["especializado", "servicios varios"]},
                "AR": {"label": "Servicios Especializados", "aliases": ["especializado", "servicios varios"]},
                "UY": {"label": "Servicios Especializados", "aliases": ["especializado"]},
                "CO": {"label": "Servicios Especializados", "aliases": ["especializado"]},
                "EC": {"label": "Servicios Especializados", "aliases": ["especializado"]},
                "PE": {"label": "Servicios Especializados", "aliases": ["especializado"]},
                "VE": {"label": "Servicios Especializados", "aliases": ["especializado"]},
                "US": {"label": "Specialized Services", "aliases": ["specialized", "various services"]},
                "BR": {"label": "Serviços Especializados", "aliases": ["especializado"]},
            },
        }

        # Leer archivo JSON
        json_full_path = os.path.join(settings.BASE_DIR, json_path) if not os.path.isabs(json_path) else json_path
        
        try:
            with open(json_full_path, 'r', encoding='utf-8') as f:
                servicios_data = json.load(f)
            self.stdout.write(self.style.SUCCESS(f"[INFO] Archivo JSON leído: {len(servicios_data)} servicios encontrados"))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"[ERROR] No se encontró el archivo {json_full_path}"))
            return
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f"[ERROR] JSON inválido en {json_full_path}: {e}"))
            return

        servicios_creados = 0
        servicios_actualizados = 0
        nombres_creados = 0

        # Procesar cada servicio del JSON
        for item in servicios_data:
            code = item.get("code", "")
            category = item.get("category", "mantenimiento")
            translations = item.get("translations", {})

            if not code or not translations:
                self.stdout.write(self.style.WARNING(f"[WARN] Saltando servicio sin código o traducciones: {item.get('code', 'sin código')}"))
                continue

            # Crear categorías para cada país
            categorias_por_pais = {}
            for country in paises_config.keys():
                if category in categorias_config:
                    try:
                        if dry_run:
                            # En dry-run, intentamos obtener o simular
                            try:
                                categoria = CategoriaServicio.objects.get(code=category, country=country)
                            except CategoriaServicio.DoesNotExist:
                                # Simulamos que existe para dry-run creando un objeto simple
                                class CategoriaMock:
                                    def __init__(self, code, country):
                                        self.code = code
                                        self.country = country
                                        self.id = None
                                categoria = CategoriaMock(category, country)
                        else:
                            categoria, created = CategoriaServicio.objects.get_or_create(
                                code=category,
                                country=country,
                                defaults={}
                            )

                            # Crear nombre de categoría solo si la categoría fue creada o si no existe el nombre
                            if country in categorias_config[category]:
                                cat_info = categorias_config[category][country]
                                language = paises_config[country]

                                CategoriaServicioName.objects.update_or_create(
                                    categoria=categoria,
                                    language=language,
                                    is_default=True,
                                    defaults={
                                        "label": cat_info["label"],
                                        "aliases": cat_info.get("aliases", []),
                                    }
                                )

                        categorias_por_pais[country] = categoria
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"[ERROR] Error creando categoría {category} para {country}: {e}"))
                        categorias_por_pais[country] = None

            # Obtener nombre base (preferir US, luego CL, luego el primero disponible)
            nombre_base = None
            for preferred in ["US", "CL"]:
                if preferred in translations:
                    nombre_base = translations[preferred].get("label")
                    break
            if not nombre_base and translations:
                first_country = list(translations.keys())[0]
                nombre_base = translations[first_country].get("label")

            if not nombre_base:
                self.stdout.write(self.style.WARNING(f"[WARN] Saltando servicio {code}: no se encontró nombre base"))
                continue

            # Usar la primera categoría disponible como referencia
            primera_categoria = None
            for preferred_country in ["US", "CL"]:
                if preferred_country in categorias_por_pais and categorias_por_pais[preferred_country]:
                    primera_categoria = categorias_por_pais[preferred_country]
                    break
            if not primera_categoria and categorias_por_pais:
                primera_categoria = next((c for c in categorias_por_pais.values() if c), None)

            if not primera_categoria:
                self.stdout.write(self.style.WARNING(f"[WARN] No se pudo crear categoría para {category}, saltando servicio {code}"))
                continue

            # Crear o obtener servicio maestro
            if dry_run:
                servicio = None
                created = True  # Simulamos creación
                self.stdout.write(f"[DRY-RUN] Se crearía servicio: {nombre_base} ({code})")
            else:
                servicio, created = Servicio.objects.get_or_create(
                    nombre=nombre_base,
                    empresa_id=MASTER_ID,
                    categoria=primera_categoria,
                    defaults={}
                )

            if created:
                servicios_creados += 1
                if not dry_run:
                    self.stdout.write(self.style.SUCCESS(f"[OK] Servicio maestro creado: {nombre_base} ({code})"))
            else:
                servicios_actualizados += 1

            # Poblar nombres localizados para todos los países
            for country, language in paises_config.items():
                # Obtener traducción del país o usar fallback
                if country in translations:
                    config = translations[country]
                elif "CL" in translations:
                    config = translations["CL"]  # Fallback a Chile
                elif "US" in translations:
                    config = translations["US"]  # Fallback a USA
                else:
                    continue  # Saltar si no hay traducción disponible

                label = config.get("label", "")
                aliases = config.get("aliases", [])

                if not label:
                    continue

                # Determinar si es el nombre por defecto para este idioma
                is_default = False
                if language == "es":
                    is_default = True
                elif language == "en":
                    has_spanish = any(paises_config.get(c, "") == "es" for c in translations.keys())
                    is_default = not has_spanish
                elif language == "pt":
                    has_spanish = any(paises_config.get(c, "") == "es" for c in translations.keys())
                    has_english = any(paises_config.get(c, "") == "en" for c in translations.keys())
                    is_default = not has_spanish and not has_english

                # Crear nombre localizado con aliases regionales
                if not dry_run and servicio:
                    _, name_created = ServicioName.objects.update_or_create(
                        servicio=servicio,
                        language=language,
                        is_default=is_default,
                        defaults={
                            "label": label,
                            "aliases": aliases,  # Aliases específicos de la región
                        }
                    )

                    if name_created:
                        nombres_creados += 1

                self.stdout.write(f"   [{country}] {label} - Aliases: {', '.join(aliases[:3])}...")

        if not dry_run:
            total = Servicio.objects.filter(empresa_id=MASTER_ID).count()
            total_nombres = ServicioName.objects.filter(servicio__empresa_id=MASTER_ID).count()
        else:
            total = servicios_creados
            total_nombres = nombres_creados

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("="*70))
        self.stdout.write(self.style.SUCCESS("[OK] Catálogo maestro cargado desde JSON exitosamente."))
        self.stdout.write(self.style.SUCCESS("="*70))
        self.stdout.write(f"[RESUMEN] Resumen:")
        self.stdout.write(f"   - Servicios procesados del JSON: {len(servicios_data)}")
        self.stdout.write(f"   - Servicios creados: {servicios_creados}")
        self.stdout.write(f"   - Servicios actualizados: {servicios_actualizados}")
        self.stdout.write(f"   - Nombres localizados creados: {nombres_creados}")
        self.stdout.write(f"   - Total servicios en catálogo: {total}")
        self.stdout.write(f"   - Total nombres localizados: {total_nombres}")
        self.stdout.write(f"   - Países soportados: {', '.join(paises_config.keys())}")
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("[OK] El catálogo está listo para producción."))
        self.stdout.write(self.style.SUCCESS("   Los usuarios pueden buscar con su jerga local y encontrarán los servicios correctos."))
        self.stdout.write(self.style.SUCCESS("="*70))


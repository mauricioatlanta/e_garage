from django.core.management.base import BaseCommand

from taller.servicios.models import (CategoriaServicio, CategoriaServicioName,
                                     Servicio, ServicioName,
                                     SubcategoriaServicio,
                                     SubcategoriaServicioName)


class Command(BaseCommand):
    help = "Carga categorías, subcategorías y servicios para Chile (español) y USA (inglés)"

    def handle(self, *args, **options):
        # --- Definición de datos ---
        categorias = [
            {
                "code": "motor",
                "es": "Sistema de Motor",
                "en": "Engine System",
                "subcategorias": [
                    {
                        "code": "diagnostico",
                        "es": "Diagnóstico computarizado de motor",
                        "en": "Engine Computer Diagnostics",
                        "servicios": [
                            {
                                "es": "Diagnóstico computarizado de motor (OBD-II / fabricante)",
                                "en": "OBD-II/Manufacturer Engine Scan",
                            },
                        ],
                    },
                    {
                        "code": "aceite",
                        "es": "Cambio de aceite y filtros",
                        "en": "Oil & Filter Change",
                        "servicios": [
                            {
                                "es": "Cambio de aceite de motor y filtros (aceite, aire, combustible, habitáculo)",
                                "en": "Engine Oil & Filter Change (oil, air, fuel, cabin)",
                            }
                        ],
                    },
                    # ... Agrega aquí el resto de subcategorías y servicios del listado ...
                ],
            },
            # ... Agrega aquí el resto de categorías principales (transmisión, frenos, etc) ...
        ]

        otros_servicios = [
            {
                "code": "especiales",
                "es": "Servicios Especiales",
                "en": "Special Services",
                "servicios": [
                    {
                        "es": "Preparación para revisión técnica",
                        "en": "Inspection Prep",
                    },
                    {
                        "es": "Instalación de accesorios 4x4",
                        "en": "4x4 Accessories Install",
                    },
                    # ... Agrega el resto de otros servicios ...
                ],
            },
            {
                "code": "emergencias",
                "es": "Emergencias y Servicios Móviles",
                "en": "Emergency & Mobile Services",
                "servicios": [
                    {"es": "Asistencia en ruta", "en": "Roadside Assistance"},
                    # ... Agrega el resto de emergencias ...
                ],
            },
        ]

        # --- Proceso de carga ---
        for country, lang, label_key in [("CL", "es", "es"), ("US", "en", "en")]:
            self.stdout.write(
                self.style.NOTICE(f"Poblando servicios para {country} ({lang})")
            )
            # Categorías principales
            for cat in categorias:
                cat_obj, _ = CategoriaServicio.objects.get_or_create(
                    country=country, code=cat["code"]
                )
                CategoriaServicioName.objects.get_or_create(
                    categoria=cat_obj,
                    language=lang,
                    label=cat[label_key],
                    is_default=True,
                )
                # Subcategorías
                for sub in cat["subcategorias"]:
                    sub_obj, _ = SubcategoriaServicio.objects.get_or_create(
                        categoria=cat_obj, code=sub["code"], country=country
                    )
                    SubcategoriaServicioName.objects.get_or_create(
                        subcategoria=sub_obj,
                        language=lang,
                        label=sub[label_key],
                        is_default=True,
                    )
                    # Servicios
                    for serv in sub["servicios"]:
                        serv_obj, _ = Servicio.objects.get_or_create(
                            subcategoria=sub_obj,
                            code=serv[label_key][:48],
                            country=country,
                        )
                        ServicioName.objects.get_or_create(
                            servicio=serv_obj,
                            language=lang,
                            label=serv[label_key],
                            is_default=True,
                        )

            # Otros servicios
            for cat in otros_servicios:
                cat_obj, _ = CategoriaServicio.objects.get_or_create(
                    country=country, code=cat["code"]
                )
                CategoriaServicioName.objects.get_or_create(
                    categoria=cat_obj,
                    language=lang,
                    label=cat[label_key],
                    is_default=True,
                )
                sub_obj, _ = SubcategoriaServicio.objects.get_or_create(
                    categoria=cat_obj, code=cat["code"], country=country
                )
                SubcategoriaServicioName.objects.get_or_create(
                    subcategoria=sub_obj,
                    language=lang,
                    label=cat[label_key],
                    is_default=True,
                )
                for serv in cat["servicios"]:
                    serv_obj, _ = Servicio.objects.get_or_create(
                        subcategoria=sub_obj, code=serv[label_key][:48], country=country
                    )
                    ServicioName.objects.get_or_create(
                        servicio=serv_obj,
                        language=lang,
                        label=serv[label_key],
                        is_default=True,
                    )

        self.stdout.write(
            self.style.SUCCESS(
                "Servicios y otros servicios cargados correctamente para Chile y USA."
            )
        )

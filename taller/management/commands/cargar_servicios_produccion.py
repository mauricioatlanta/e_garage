"""
Comando para cargar servicios básicos en producción
Crea categorías, subcategorías y servicios para CL y US, y los asocia a todas las empresas existentes
"""

from django.core.management.base import BaseCommand

from taller.models import Empresa
from taller.servicios.models import (
    CategoriaServicio,
    CategoriaServicioName,
    Servicio,
    ServicioName,
    SubcategoriaServicio,
    SubcategoriaServicioName,
)


class Command(BaseCommand):
    help = "Carga categorías, subcategorías y servicios básicos para Chile (español) y USA (inglés) para todas las empresas"

    def handle(self, *args, **options):
        # Datos completos de servicios
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
                            {
                                "es": "Lectura y borrado de códigos de error",
                                "en": "Read and Clear Error Codes",
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
                            },
                            {
                                "es": "Cambio de aceite sintético",
                                "en": "Synthetic Oil Change",
                            },
                            {
                                "es": "Cambio de aceite convencional",
                                "en": "Conventional Oil Change",
                            },
                        ],
                    },
                    {
                        "code": "reparacion",
                        "es": "Reparación de motor",
                        "en": "Engine Repair",
                        "servicios": [
                            {
                                "es": "Reparación de sobrecalentamiento",
                                "en": "Overheating Repair",
                            },
                            {
                                "es": "Cambio de correa de distribución",
                                "en": "Timing Belt Replacement",
                            },
                            {
                                "es": "Cambio de cadena de distribución",
                                "en": "Timing Chain Replacement",
                            },
                            {
                                "es": "Reparación de fuga de aceite",
                                "en": "Oil Leak Repair",
                            },
                        ],
                    },
                ],
            },
            {
                "code": "frenos",
                "es": "Sistema de Frenos",
                "en": "Brake System",
                "subcategorias": [
                    {
                        "code": "revision",
                        "es": "Revisión de frenos",
                        "en": "Brake Inspection",
                        "servicios": [
                            {
                                "es": "Revisión completa del sistema de frenos",
                                "en": "Complete Brake System Inspection",
                            },
                            {
                                "es": "Revisión de pastillas y discos",
                                "en": "Brake Pads and Rotors Inspection",
                            },
                        ],
                    },
                    {
                        "code": "reparacion",
                        "es": "Reparación de frenos",
                        "en": "Brake Repair",
                        "servicios": [
                            {
                                "es": "Cambio de pastillas de freno",
                                "en": "Brake Pad Replacement",
                            },
                            {
                                "es": "Cambio de discos de freno",
                                "en": "Brake Rotor Replacement",
                            },
                            {
                                "es": "Cambio de líquido de frenos",
                                "en": "Brake Fluid Replacement",
                            },
                            {
                                "es": "Reparación de sistema ABS",
                                "en": "ABS System Repair",
                            },
                        ],
                    },
                ],
            },
            {
                "code": "transmision",
                "es": "Transmisión",
                "en": "Transmission",
                "subcategorias": [
                    {
                        "code": "mantenimiento",
                        "es": "Mantenimiento de transmisión",
                        "en": "Transmission Maintenance",
                        "servicios": [
                            {
                                "es": "Cambio de aceite de transmisión automática",
                                "en": "Automatic Transmission Fluid Change",
                            },
                            {
                                "es": "Cambio de aceite de caja manual",
                                "en": "Manual Transmission Fluid Change",
                            },
                        ],
                    },
                    {
                        "code": "reparacion",
                        "es": "Reparación de transmisión",
                        "en": "Transmission Repair",
                        "servicios": [
                            {
                                "es": "Reparación de transmisión automática",
                                "en": "Automatic Transmission Repair",
                            },
                            {
                                "es": "Cambio de kit de embrague",
                                "en": "Clutch Kit Replacement",
                            },
                        ],
                    },
                ],
            },
            {
                "code": "suspension",
                "es": "Suspensión y Dirección",
                "en": "Suspension & Steering",
                "subcategorias": [
                    {
                        "code": "alineacion",
                        "es": "Alineación",
                        "en": "Alignment",
                        "servicios": [
                            {
                                "es": "Alineación de ruedas delantera",
                                "en": "Front Wheel Alignment",
                            },
                            {
                                "es": "Alineación completa de 4 ruedas",
                                "en": "4-Wheel Alignment",
                            },
                        ],
                    },
                    {
                        "code": "reparacion",
                        "es": "Reparación de suspensión",
                        "en": "Suspension Repair",
                        "servicios": [
                            {
                                "es": "Cambio de amortiguadores",
                                "en": "Shock Absorber Replacement",
                            },
                            {
                                "es": "Cambio de rótulas",
                                "en": "Ball Joint Replacement",
                            },
                        ],
                    },
                ],
            },
            {
                "code": "electrico",
                "es": "Sistema Eléctrico",
                "en": "Electrical System",
                "subcategorias": [
                    {
                        "code": "bateria",
                        "es": "Batería y carga",
                        "en": "Battery & Charging",
                        "servicios": [
                            {
                                "es": "Cambio de batería",
                                "en": "Battery Replacement",
                            },
                            {
                                "es": "Prueba de batería y alternador",
                                "en": "Battery and Alternator Test",
                            },
                        ],
                    },
                    {
                        "code": "luces",
                        "es": "Sistema de iluminación",
                        "en": "Lighting System",
                        "servicios": [
                            {
                                "es": "Cambio de focos y ampolletas",
                                "en": "Bulb Replacement",
                            },
                            {
                                "es": "Instalación de luces LED",
                                "en": "LED Light Installation",
                            },
                        ],
                    },
                ],
            },
        ]

        otros_servicios = [
            {
                "code": "especiales",
                "es": "Servicios Especiales",
                "en": "Special Services",
                "servicios": [
                    {"es": "Preparación para revisión técnica", "en": "Inspection Prep"},
                    {"es": "Instalación de accesorios 4x4", "en": "4x4 Accessories Install"},
                    {"es": "Lavado y detallado", "en": "Wash & Detail"},
                ],
            },
            {
                "code": "emergencias",
                "es": "Emergencias y Servicios Móviles",
                "en": "Emergency & Mobile Services",
                "servicios": [
                    {"es": "Asistencia en ruta", "en": "Roadside Assistance"},
                    {"es": "Servicio móvil a domicilio", "en": "Mobile Service"},
                ],
            },
        ]

        # Obtener todas las empresas
        empresas = Empresa.objects.all()
        if not empresas.exists():
            self.stdout.write(
                self.style.WARNING(
                    "⚠️ No hay empresas en la base de datos. Los servicios requieren una empresa."
                )
            )
            return

        self.stdout.write(
            self.style.NOTICE(f"📋 Encontradas {empresas.count()} empresa(s) en la base de datos")
        )

        # Proceso de carga para cada país
        for country, lang, label_key in [("CL", "es", "es"), ("US", "en", "en")]:
            self.stdout.write(self.style.NOTICE(f"\n🌍 Poblando servicios para {country} ({lang})"))

            # Categorías principales
            for cat in categorias:
                cat_obj, created = CategoriaServicio.objects.get_or_create(
                    country=country, code=cat["code"]
                )
                CategoriaServicioName.objects.get_or_create(
                    categoria=cat_obj,
                    language=lang,
                    is_default=True,
                    defaults={"label": cat[label_key]},
                )
                if created:
                    self.stdout.write(f"  ✅ Categoría creada: {cat[label_key]}")

                # Subcategorías
                for sub in cat["subcategorias"]:
                    sub_obj, created = SubcategoriaServicio.objects.get_or_create(
                        categoria=cat_obj, code=sub["code"], country=country
                    )
                    SubcategoriaServicioName.objects.get_or_create(
                        subcategoria=sub_obj,
                        language=lang,
                        is_default=True,
                        defaults={"label": sub[label_key]},
                    )

                    # Servicios para cada empresa
                    for serv in sub["servicios"]:
                        serv_code = serv[label_key][:48].replace(" ", "_").upper()
                        for empresa in empresas:
                            # Solo crear servicios para empresas del país correspondiente
                            if empresa.pais == country:
                                # Primero intentar obtener el servicio existente (sin subcategoría en la búsqueda)
                                # porque la restricción UNIQUE es sobre empresa, nombre, categoria
                                try:
                                    servicio = Servicio.objects.get(
                                        empresa=empresa,
                                        categoria=cat_obj,
                                        nombre=serv[label_key],
                                    )
                                    # Si existe, actualizar subcategoría si es necesario
                                    if servicio.subcategoria != sub_obj:
                                        servicio.subcategoria = sub_obj
                                        servicio.save()
                                except Servicio.DoesNotExist:
                                    # Si no existe, crearlo
                                    try:
                                        servicio = Servicio.objects.create(
                                            empresa=empresa,
                                            categoria=cat_obj,
                                            subcategoria=sub_obj,
                                            nombre=serv[label_key],
                                        )
                                    except Exception as e:
                                        # Si hay error de integridad, continuar
                                        self.stdout.write(
                                            self.style.WARNING(
                                                f"  ⚠️ Error al crear servicio '{serv[label_key]}' para {empresa.nombre_taller or empresa.empresa or f'Empresa {empresa.id}'}: {str(e)[:100]}"
                                            )
                                        )
                                        continue

                                # Crear o actualizar el nombre localizado
                                ServicioName.objects.get_or_create(
                                    servicio=servicio,
                                    language=lang,
                                    is_default=True,
                                    defaults={"label": serv[label_key]},
                                )

            # Otros servicios
            for cat in otros_servicios:
                cat_obj, created = CategoriaServicio.objects.get_or_create(
                    country=country, code=cat["code"]
                )
                CategoriaServicioName.objects.get_or_create(
                    categoria=cat_obj,
                    language=lang,
                    is_default=True,
                    defaults={"label": cat[label_key]},
                )
                sub_obj, created = SubcategoriaServicio.objects.get_or_create(
                    categoria=cat_obj, code=cat["code"], country=country
                )
                SubcategoriaServicioName.objects.get_or_create(
                    subcategoria=sub_obj,
                    language=lang,
                    is_default=True,
                    defaults={"label": cat[label_key]},
                )
                for serv in cat["servicios"]:
                    for empresa in empresas:
                        if empresa.pais == country:
                            # Primero intentar obtener el servicio existente
                            try:
                                servicio = Servicio.objects.get(
                                    empresa=empresa,
                                    categoria=cat_obj,
                                    nombre=serv[label_key],
                                )
                                # Si existe, actualizar subcategoría si es necesario
                                if servicio.subcategoria != sub_obj:
                                    servicio.subcategoria = sub_obj
                                    servicio.save()
                            except Servicio.DoesNotExist:
                                # Si no existe, crearlo
                                try:
                                    servicio = Servicio.objects.create(
                                        empresa=empresa,
                                        categoria=cat_obj,
                                        subcategoria=sub_obj,
                                        nombre=serv[label_key],
                                    )
                                except Exception as e:
                                    # Si hay error, continuar
                                    continue

                            # Crear o actualizar el nombre localizado
                            ServicioName.objects.get_or_create(
                                servicio=servicio,
                                language=lang,
                                is_default=True,
                                defaults={"label": serv[label_key]},
                            )

        # Resumen final
        total_categorias = CategoriaServicio.objects.count()
        total_subcategorias = SubcategoriaServicio.objects.count()
        total_servicios = Servicio.objects.count()

        self.stdout.write(self.style.SUCCESS("\n✅ ¡Carga completada!"))
        self.stdout.write(f"📊 Resumen:")
        self.stdout.write(f"   Categorías: {total_categorias}")
        self.stdout.write(f"   Subcategorías: {total_subcategorias}")
        self.stdout.write(f"   Servicios: {total_servicios}")

        # Mostrar servicios por empresa
        for empresa in empresas:
            servicios_count = Servicio.objects.filter(empresa=empresa).count()
            nombre_empresa = empresa.nombre_taller or empresa.empresa or f"Empresa {empresa.id}"
            self.stdout.write(f"   {nombre_empresa} ({empresa.pais}): {servicios_count} servicios")

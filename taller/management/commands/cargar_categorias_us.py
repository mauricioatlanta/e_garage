from django.core.management.base import BaseCommand

from taller.servicios.models import (
    CategoriaServicio,
    CategoriaServicioName,
    SubcategoriaServicio,
    SubcategoriaServicioName,
)


class Command(BaseCommand):
    help = "Carga categorías y subcategorías básicas para USA (inglés)"

    def handle(self, *args, **options):
        country = "US"
        language = "en"

        # Categorías básicas para USA
        categorias_data = [
            {
                "code": "ENGINE",
                "label": "Engine System",
                "subcategorias": [
                    {"code": "DIAGNOSTICS", "label": "Engine Diagnostics"},
                    {"code": "OIL_SERVICE", "label": "Oil & Filter Service"},
                    {"code": "COOLING", "label": "Cooling System"},
                    {"code": "FUEL", "label": "Fuel System"},
                    {"code": "IGNITION", "label": "Ignition System"},
                ],
            },
            {
                "code": "TRANSMISSION",
                "label": "Transmission & Drivetrain",
                "subcategorias": [
                    {"code": "AUTOMATIC", "label": "Automatic Transmission"},
                    {"code": "MANUAL", "label": "Manual Transmission"},
                    {"code": "DRIVETRAIN", "label": "Drivetrain Service"},
                ],
            },
            {
                "code": "BRAKES",
                "label": "Brake System",
                "subcategorias": [
                    {"code": "BRAKE_PADS", "label": "Brake Pads & Rotors"},
                    {"code": "BRAKE_FLUID", "label": "Brake Fluid Service"},
                    {"code": "BRAKE_LINES", "label": "Brake Lines & Hoses"},
                ],
            },
            {
                "code": "SUSPENSION",
                "label": "Suspension & Steering",
                "subcategorias": [
                    {"code": "ALIGNMENT", "label": "Wheel Alignment"},
                    {"code": "SHOCKS", "label": "Shocks & Struts"},
                    {"code": "STEERING", "label": "Steering Components"},
                ],
            },
            {
                "code": "ELECTRICAL",
                "label": "Electrical System",
                "subcategorias": [
                    {"code": "BATTERY", "label": "Battery Service"},
                    {"code": "ALTERNATOR", "label": "Alternator & Starter"},
                    {"code": "LIGHTING", "label": "Lighting Systems"},
                ],
            },
            {
                "code": "MAINTENANCE",
                "label": "General Maintenance",
                "subcategorias": [
                    {"code": "INSPECTION", "label": "Vehicle Inspection"},
                    {"code": "FLUIDS", "label": "Fluid Service"},
                    {"code": "FILTERS", "label": "Filter Replacement"},
                ],
            },
        ]

        self.stdout.write(
            self.style.NOTICE(f"Loading categories and subcategories for {country} ({language})...")
        )

        total_categorias = 0
        total_subcategorias = 0

        for cat_data in categorias_data:
            # Crear categoría
            categoria, created = CategoriaServicio.objects.get_or_create(
                country=country, code=cat_data["code"]
            )

            if created:
                total_categorias += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Created category: {cat_data['label']} ({cat_data['code']})"
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠️  Category already exists: {cat_data['label']} ({cat_data['code']})"
                    )
                )

            # Crear nombre de categoría
            CategoriaServicioName.objects.get_or_create(
                categoria=categoria,
                language=language,
                is_default=True,
                defaults={"label": cat_data["label"]},
            )

            # Crear subcategorías
            for sub_data in cat_data["subcategorias"]:
                subcategoria, created = SubcategoriaServicio.objects.get_or_create(
                    categoria=categoria, code=sub_data["code"], country=country
                )

                if created:
                    total_subcategorias += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"   ✅ Created subcategory: {sub_data['label']} ({sub_data['code']})"
                        )
                    )

                # Crear nombre de subcategoría
                SubcategoriaServicioName.objects.get_or_create(
                    subcategoria=subcategoria,
                    language=language,
                    is_default=True,
                    defaults={"label": sub_data["label"]},
                )

        self.stdout.write(self.style.SUCCESS("\n" + "=" * 60))
        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Successfully loaded {total_categorias} categories and {total_subcategorias} subcategories for {country}"
            )
        )
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(
            self.style.NOTICE(
                "\n💡 Tip: Now you can add services to these categories using the 'Add New Service' button."
            )
        )

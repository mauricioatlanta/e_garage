"""
Comando para cargar catálogo demo de repuestos y servicios con I18N
"""

from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand

from taller.models import Part, PartI18N, PartPrice, Service, ServiceI18N, ServicePrice, TaxPolicy


class Command(BaseCommand):
    help = "Carga catálogo demo de repuestos y servicios con I18N y precios"

    def handle(self, *args, **options):
        self.stdout.write("[CATALOGO] Cargando políticas de impuestos...")

        # === POLÍTICAS DE IMPUESTOS ===

        # Chile: IVA 19% solo a repuestos
        tax_cl_parts, _ = TaxPolicy.objects.get_or_create(
            country="CL",
            state_code="",
            applies_to="parts",
            defaults={
                "rate": Decimal("0.1900"),
                "inclusive": False,
                "active": True,
            },
        )
        self.stdout.write(f"  [OK] Chile - IVA 19% repuestos")

        # USA: Sales tax por estado (ejemplo: California 7.25%)
        tax_us_ca, _ = TaxPolicy.objects.get_or_create(
            country="US",
            state_code="CA",
            applies_to="both",
            defaults={
                "rate": Decimal("0.0725"),
                "inclusive": False,
                "active": True,
            },
        )
        self.stdout.write(f"  [OK] USA California - Sales tax 7.25% ambos")

        # Brasil: ICMS 18% repuestos
        tax_br_parts, _ = TaxPolicy.objects.get_or_create(
            country="BR",
            state_code="",
            applies_to="parts",
            defaults={
                "rate": Decimal("0.1800"),
                "inclusive": False,
                "active": True,
            },
        )
        self.stdout.write(f"  [OK] Brasil - ICMS 18% repuestos")

        # Perú: IGV 18% ambos
        tax_pe_both, _ = TaxPolicy.objects.get_or_create(
            country="PE",
            state_code="",
            applies_to="both",
            defaults={
                "rate": Decimal("0.1800"),
                "inclusive": False,
                "active": True,
            },
        )
        self.stdout.write(f"  [OK] Peru - IGV 18% ambos")

        # Venezuela: IVA 16% ambos
        tax_ve_both, _ = TaxPolicy.objects.get_or_create(
            country="VE",
            state_code="",
            applies_to="both",
            defaults={
                "rate": Decimal("0.1600"),
                "inclusive": False,
                "active": True,
            },
        )
        self.stdout.write(f"  [OK] Venezuela - IVA 16% ambos")

        self.stdout.write("")
        self.stdout.write("[REPUESTOS] Cargando repuestos demo...")

        # === REPUESTOS ===

        # Aceite de Motor 5W30
        part_oil, created = Part.objects.get_or_create(
            sku="OIL-5W30-4L",
            defaults={
                "category": "lubricantes",
                "brand": "Mobil",
                "unit": "lt",
                "weight_kg": Decimal("3.800"),
                "purchase_price": Decimal("15000.00"),
                "stock_quantity": Decimal("50.00"),
                "stock_min": Decimal("10.00"),
                "active": True,
            },
        )
        if created:
            # I18N para aceite
            PartI18N.objects.create(
                part=part_oil,
                locale="es-CL",
                display_name="Aceite de Motor 5W30 4L",
                synonyms="aceite motor, lubricante, oil",
            )
            PartI18N.objects.create(
                part=part_oil,
                locale="en-US",
                display_name="Engine Oil 5W30 4L",
                synonyms="motor oil, lubricant",
            )
            PartI18N.objects.create(
                part=part_oil,
                locale="pt-BR",
                display_name="Óleo de Motor 5W30 4L",
                synonyms="óleo motor, lubrificante",
            )
            PartI18N.objects.create(
                part=part_oil,
                locale="es-PE",
                display_name="Aceite para Motor 5W30 4L",
                synonyms="aceite motor, lubricante",
            )
            PartI18N.objects.create(
                part=part_oil,
                locale="es-VE",
                display_name="Aceite de Motor 5W30 4L",
                synonyms="aceite motor, lubricante",
            )
            self.stdout.write(f"  [OK] {part_oil.sku} + I18N (5 locales)")

        # Filtro de Aceite
        part_filter, created = Part.objects.get_or_create(
            sku="FILTER-OIL-STD",
            defaults={
                "category": "filtros",
                "brand": "Bosch",
                "unit": "un",
                "weight_kg": Decimal("0.250"),
                "purchase_price": Decimal("3000.00"),
                "stock_quantity": Decimal("100.00"),
                "stock_min": Decimal("20.00"),
                "active": True,
            },
        )
        if created:
            PartI18N.objects.create(
                part=part_filter,
                locale="es-CL",
                display_name="Filtro de Aceite",
                synonyms="filtro aceite, oil filter",
            )
            PartI18N.objects.create(
                part=part_filter, locale="en-US", display_name="Oil Filter", synonyms="filter, oil"
            )
            PartI18N.objects.create(
                part=part_filter,
                locale="pt-BR",
                display_name="Filtro de Óleo",
                synonyms="filtro óleo",
            )
            PartI18N.objects.create(
                part=part_filter, locale="es-PE", display_name="Filtro de Aceite", synonyms="filtro"
            )
            PartI18N.objects.create(
                part=part_filter, locale="es-VE", display_name="Filtro de Aceite", synonyms="filtro"
            )
            self.stdout.write(f"  [OK] {part_filter.sku} + I18N (5 locales)")

        # Pastillas de Freno
        part_brake, created = Part.objects.get_or_create(
            sku="BRAKE-PAD-FRONT",
            defaults={
                "category": "frenos",
                "brand": "Brembo",
                "unit": "set",
                "weight_kg": Decimal("1.200"),
                "purchase_price": Decimal("25000.00"),
                "stock_quantity": Decimal("30.00"),
                "stock_min": Decimal("5.00"),
                "active": True,
            },
        )
        if created:
            PartI18N.objects.create(
                part=part_brake,
                locale="es-CL",
                display_name="Pastillas de Freno Delanteras",
                synonyms="pastillas freno, brake pads",
            )
            PartI18N.objects.create(
                part=part_brake,
                locale="en-US",
                display_name="Front Brake Pads",
                synonyms="brake pads, front pads",
            )
            PartI18N.objects.create(
                part=part_brake,
                locale="pt-BR",
                display_name="Pastilhas de Freio Dianteiras",
                synonyms="pastilhas freio",
            )
            PartI18N.objects.create(
                part=part_brake,
                locale="es-PE",
                display_name="Pastillas de Freno Delanteras",
                synonyms="pastillas",
            )
            PartI18N.objects.create(
                part=part_brake,
                locale="es-VE",
                display_name="Pastillas de Freno Delanteras",
                synonyms="pastillas",
            )
            self.stdout.write(f"  [OK] {part_brake.sku} + I18N (5 locales)")

        self.stdout.write("")
        self.stdout.write("[SERVICIOS] Cargando servicios demo...")

        # === SERVICIOS ===

        # Cambio de Aceite
        service_oil, created = Service.objects.get_or_create(
            code="OIL_CHANGE",
            defaults={
                "category": "maintenance",
                "std_hours": Decimal("0.50"),
                "active": True,
            },
        )
        if created:
            ServiceI18N.objects.create(
                service=service_oil,
                locale="es-CL",
                display_name="Cambio de Aceite",
                synonyms="cambio aceite, oil change",
            )
            ServiceI18N.objects.create(
                service=service_oil,
                locale="en-US",
                display_name="Oil Change",
                synonyms="oil service, lube",
            )
            ServiceI18N.objects.create(
                service=service_oil,
                locale="pt-BR",
                display_name="Troca de Óleo",
                synonyms="troca óleo, lubrificação",
            )
            ServiceI18N.objects.create(
                service=service_oil,
                locale="es-PE",
                display_name="Cambio de Aceite",
                synonyms="cambio aceite",
            )
            ServiceI18N.objects.create(
                service=service_oil,
                locale="es-VE",
                display_name="Cambio de Aceite",
                synonyms="cambio aceite",
            )
            self.stdout.write(f"  [OK] {service_oil.code} + I18N (5 locales)")

        # Servicio de Frenos
        service_brake, created = Service.objects.get_or_create(
            code="BRAKE_SERVICE",
            defaults={
                "category": "repair",
                "std_hours": Decimal("2.00"),
                "active": True,
            },
        )
        if created:
            ServiceI18N.objects.create(
                service=service_brake,
                locale="es-CL",
                display_name="Servicio de Frenos",
                synonyms="frenos, brake service",
            )
            ServiceI18N.objects.create(
                service=service_brake,
                locale="en-US",
                display_name="Brake Service",
                synonyms="brake repair, brakes",
            )
            ServiceI18N.objects.create(
                service=service_brake,
                locale="pt-BR",
                display_name="Serviço de Freios",
                synonyms="freios, manutenção freios",
            )
            ServiceI18N.objects.create(
                service=service_brake,
                locale="es-PE",
                display_name="Servicio de Frenos",
                synonyms="frenos",
            )
            ServiceI18N.objects.create(
                service=service_brake,
                locale="es-VE",
                display_name="Servicio de Frenos",
                synonyms="frenos",
            )
            self.stdout.write(f"  [OK] {service_brake.code} + I18N (5 locales)")

        # Alineación y Balanceo
        service_alignment, created = Service.objects.get_or_create(
            code="ALIGNMENT_BALANCE",
            defaults={
                "category": "maintenance",
                "std_hours": Decimal("1.00"),
                "active": True,
            },
        )
        if created:
            ServiceI18N.objects.create(
                service=service_alignment,
                locale="es-CL",
                display_name="Alineación y Balanceo",
                synonyms="alineación, balanceo, alignment",
            )
            ServiceI18N.objects.create(
                service=service_alignment,
                locale="en-US",
                display_name="Wheel Alignment & Balance",
                synonyms="alignment, balance, wheel service",
            )
            ServiceI18N.objects.create(
                service=service_alignment,
                locale="pt-BR",
                display_name="Alinhamento e Balanceamento",
                synonyms="alinhamento, balanceamento",
            )
            ServiceI18N.objects.create(
                service=service_alignment,
                locale="es-PE",
                display_name="Alineación y Balanceo",
                synonyms="alineación, balanceo",
            )
            ServiceI18N.objects.create(
                service=service_alignment,
                locale="es-VE",
                display_name="Alineación y Balanceo",
                synonyms="alineación, balanceo",
            )
            self.stdout.write(f"  [OK] {service_alignment.code} + I18N (5 locales)")

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("[CATALOGO] Catálogo demo cargado exitosamente!"))
        self.stdout.write("")
        self.stdout.write("Para cargar precios por empresa, usa:")
        self.stdout.write(
            "  PartPrice.objects.create(part=part, company=empresa, currency='CLP', price=20000, valid_from=date.today())"
        )
        self.stdout.write(
            "  ServicePrice.objects.create(service=service, company=empresa, currency='CLP', price=15000, valid_from=date.today())"
        )

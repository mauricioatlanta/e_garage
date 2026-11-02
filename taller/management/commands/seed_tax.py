# -*- coding: utf-8 -*-
"""
Comando para crear semillas mínimas de TaxPolicy

Convenciones del proyecto:
- Chile: IVA 19% solo a repuestos (NO servicios)
- USA: sales tax por estado (ejemplo: GA 4%)
- Brasil: ICMS 18% solo repuestos
- Perú: IGV 18% ambos (repuestos y servicios)
- Venezuela: IVA 16% ambos (repuestos y servicios)

Ejecutar:
  python manage.py seed_tax
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from taller.models import TaxPolicy


class Command(BaseCommand):
    help = "Crea políticas de impuestos mínimas para todos los países soportados"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Actualizar políticas existentes",
        )

    def handle(self, *args, **options):
        force = options.get("force", False)

        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("[SEED] Creando políticas de impuestos base")
        self.stdout.write("=" * 80 + "\n")

        created_count = 0
        updated_count = 0
        skipped_count = 0

        # === POLÍTICAS BASE POR PAÍS ===

        policies = [
            # --- CHILE ---
            # CONVENCIÓN: IVA 19% SOLO a repuestos (NO servicios)
            {
                "country": "CL",
                "state_code": "",
                "city_name": "",
                "applies_to": "parts",
                "defaults": {
                    "rate": Decimal("0.1900"),
                    "inclusive": False,
                    "active": True,
                },
            },
            # Chile servicios: 0% (no se crea política, fallback es 0)
            # --- USA ---
            # Ejemplos de sales tax por estado
            # Georgia: 4%
            {
                "country": "US",
                "state_code": "GA",
                "city_name": "",
                "applies_to": "both",
                "defaults": {
                    "rate": Decimal("0.0400"),
                    "inclusive": False,
                    "active": True,
                },
            },
            # California: 7.25%
            {
                "country": "US",
                "state_code": "CA",
                "city_name": "",
                "applies_to": "both",
                "defaults": {
                    "rate": Decimal("0.0725"),
                    "inclusive": False,
                    "active": True,
                },
            },
            # New York: 4%
            {
                "country": "US",
                "state_code": "NY",
                "city_name": "",
                "applies_to": "both",
                "defaults": {
                    "rate": Decimal("0.0400"),
                    "inclusive": False,
                    "active": True,
                },
            },
            # Florida: 6%
            {
                "country": "US",
                "state_code": "FL",
                "city_name": "",
                "applies_to": "both",
                "defaults": {
                    "rate": Decimal("0.0600"),
                    "inclusive": False,
                    "active": True,
                },
            },
            # Texas: 6.25%
            {
                "country": "US",
                "state_code": "TX",
                "city_name": "",
                "applies_to": "both",
                "defaults": {
                    "rate": Decimal("0.0625"),
                    "inclusive": False,
                    "active": True,
                },
            },
            # --- BRASIL ---
            # ICMS 18% solo repuestos
            {
                "country": "BR",
                "state_code": "",
                "city_name": "",
                "applies_to": "parts",
                "defaults": {
                    "rate": Decimal("0.1800"),
                    "inclusive": False,
                    "active": True,
                },
            },
            # --- PERÚ ---
            # IGV 18% ambos (repuestos y servicios)
            {
                "country": "PE",
                "state_code": "",
                "city_name": "",
                "applies_to": "both",
                "defaults": {
                    "rate": Decimal("0.1800"),
                    "inclusive": False,
                    "active": True,
                },
            },
            # --- VENEZUELA ---
            # IVA 16% ambos (repuestos y servicios)
            {
                "country": "VE",
                "state_code": "",
                "city_name": "",
                "applies_to": "both",
                "defaults": {
                    "rate": Decimal("0.1600"),
                    "inclusive": False,
                    "active": True,
                },
            },
        ]

        # Crear o actualizar políticas
        for policy_data in policies:
            # Separar lookup keys de defaults
            lookup = {
                "country": policy_data["country"],
                "state_code": policy_data["state_code"],
                "city_name": policy_data["city_name"],
                "applies_to": policy_data["applies_to"],
            }

            defaults = policy_data["defaults"]

            # Intentar crear o obtener
            policy, created = TaxPolicy.objects.get_or_create(**lookup, defaults=defaults)

            if created:
                created_count += 1
                scope = self._format_scope(lookup)
                rate_pct = float(defaults["rate"] * 100)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  [CREADO] {scope} -> {lookup['applies_to']} {rate_pct:.2f}%"
                    )
                )
            else:
                # Ya existe
                if force:
                    # Actualizar si force=True
                    for key, value in defaults.items():
                        setattr(policy, key, value)
                    policy.save()
                    updated_count += 1

                    scope = self._format_scope(lookup)
                    rate_pct = float(defaults["rate"] * 100)
                    self.stdout.write(
                        self.style.WARNING(
                            f"  [ACTUALIZADO] {scope} -> {lookup['applies_to']} {rate_pct:.2f}%"
                        )
                    )
                else:
                    skipped_count += 1
                    scope = self._format_scope(lookup)
                    self.stdout.write(f"  [EXISTE] {scope}")

        # === RESUMEN ===
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("[RESUMEN] Seed TaxPolicy completado")
        self.stdout.write("=" * 80)

        self.stdout.write(f"\n  Políticas creadas: {created_count}")
        self.stdout.write(f"  Políticas actualizadas: {updated_count}")
        self.stdout.write(f"  Políticas ya existentes: {skipped_count}")
        self.stdout.write(f"  Total procesadas: {len(policies)}")

        self.stdout.write("\n" + self.style.SUCCESS("[EXITO] Seed TaxPolicy OK"))

        # === CONVENCIONES VERIFICADAS ===
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("[CONVENCIONES] Verificación")
        self.stdout.write("=" * 80 + "\n")

        # Verificar Chile
        cl_parts = TaxPolicy.objects.filter(country="CL", applies_to="parts").first()
        cl_services = TaxPolicy.objects.filter(country="CL", applies_to="services").first()

        if cl_parts and cl_parts.rate == Decimal("0.19"):
            self.stdout.write(self.style.SUCCESS("  [OK] Chile: IVA 19% repuestos"))
        else:
            self.stdout.write(self.style.ERROR("  [ERROR] Chile: IVA repuestos incorrecto"))

        if not cl_services:
            self.stdout.write(self.style.SUCCESS("  [OK] Chile: Sin IVA en servicios (correcto)"))
        else:
            self.stdout.write(
                self.style.WARNING("  [WARN] Chile: Existe politica para servicios (revisar)")
            )

        # Verificar Perú
        pe_policy = TaxPolicy.objects.filter(country="PE", applies_to="both").first()
        if pe_policy and pe_policy.rate == Decimal("0.18"):
            self.stdout.write(self.style.SUCCESS("  [OK] Peru: IGV 18% ambos"))

        # Verificar Venezuela
        ve_policy = TaxPolicy.objects.filter(country="VE", applies_to="both").first()
        if ve_policy and ve_policy.rate == Decimal("0.16"):
            self.stdout.write(self.style.SUCCESS("  [OK] Venezuela: IVA 16% ambos"))

        # Verificar Brasil
        br_policy = TaxPolicy.objects.filter(country="BR", applies_to="parts").first()
        if br_policy and br_policy.rate == Decimal("0.18"):
            self.stdout.write(self.style.SUCCESS("  [OK] Brasil: ICMS 18% repuestos"))

        # Verificar USA
        us_count = TaxPolicy.objects.filter(country="US").count()
        if us_count >= 3:
            self.stdout.write(self.style.SUCCESS(f"  [OK] USA: {us_count} estados configurados"))

        self.stdout.write("\n" + "=" * 80 + "\n")

    def _format_scope(self, lookup):
        """Formatear alcance de la política"""
        scope = lookup["country"]
        if lookup["state_code"]:
            scope += f"-{lookup['state_code']}"
        if lookup["city_name"]:
            scope += f"-{lookup['city_name']}"
        return scope

"""
eGarage Validation Center — management command.

Creates 10 permanent demo companies (one per product profile combination)
for development, QA, demo recordings, and visual regression testing.

Usage:
    python manage.py create_validation_center          # create/update all
    python manage.py create_validation_center --list   # show table only
    python manage.py create_validation_center --reset  # delete and recreate

Each company gets:
  - A dedicated user  (username / password listed below)
  - Empresa (Chile, plan=growth, suscripcion_activa)
  - ConfiguracionEmpresa with rubro_principal + optional rubros[]
  - 3 Clientes
  - Repuestos / VehiculoDesarme / Documentos relevant to the profile

Credentials (all passwords: vc1234)
  01 vc_taller            Taller Mecánico        WORKSHOP
  02 vc_desarme           Desarmaduría           DESARMADURIA
  03 vc_repuestos         Casa de Repuestos      PARTS
  04 vc_desarme_taller    Desarmaduría + Taller  DESARMADURIA + [WORKSHOP]
  05 vc_repuestos_taller  Repuestos + Taller     PARTS + [WORKSHOP]
  06 vc_carwash           Carwash / Detailing    DETAILING
  07 vc_vulcanizacion     Vulcanización          TIRE
  08 vc_escapes           Escapes / Mufflers     EXHAUST
  09 vc_flotas            Mantención Flotas      FLEET
  10 vc_enterprise        Full Enterprise        MIXED (multi-rubro)
"""
from __future__ import annotations

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from taller.models.marca import Marca
from taller.models.modelo import Modelo
from taller.models import (
    Cliente,
    Documento,
    Empresa,
    VehiculoDesarme,
)
from taller.models.configuracion import ConfiguracionEmpresa
from taller.models.repuesto import Repuesto
from taller.utils.plan_catalog import PLAN_GROWTH

VC_PASSWORD = "vc1234"

# ---------------------------------------------------------------------------
# Profile declarations
# ---------------------------------------------------------------------------

PROFILES = [
    {
        "slot":          "01",
        "username":      "vc_taller",
        "display":       "Demo Taller Mecánico",
        "nombre_taller": "Demo Taller AutoShop",
        "rubro":         "WORKSHOP",
        "rubros_extra":  [],
        "tagline":       "Taller mecánico integral — entorno de validación",
        "with_desarme":  False,
        "with_repuestos": True,
    },
    {
        "slot":          "02",
        "username":      "vc_desarme",
        "display":       "Demo Desarmaduría",
        "nombre_taller": "Demo Desarme Norte",
        "rubro":         "DESARMADURIA",
        "rubros_extra":  [],
        "tagline":       "Desarmaduría y venta de repuestos usados",
        "with_desarme":  True,
        "with_repuestos": True,
    },
    {
        "slot":          "03",
        "username":      "vc_repuestos",
        "display":       "Demo Casa Repuestos",
        "nombre_taller": "Demo Repuestos Sur",
        "rubro":         "PARTS",
        "rubros_extra":  [],
        "tagline":       "Casa de repuestos automotrices",
        "with_desarme":  False,
        "with_repuestos": True,
    },
    {
        "slot":          "04",
        "username":      "vc_desarme_taller",
        "display":       "Demo Desarmaduría + Taller",
        "nombre_taller": "Demo Desarme + Taller Oriente",
        "rubro":         "DESARMADURIA",
        "rubros_extra":  ["WORKSHOP"],
        "tagline":       "Desarmaduría con taller de reparación integrado",
        "with_desarme":  True,
        "with_repuestos": True,
    },
    {
        "slot":          "05",
        "username":      "vc_repuestos_taller",
        "display":       "Demo Repuestos + Taller",
        "nombre_taller": "Demo Repuestos & Mecánica Poniente",
        "rubro":         "PARTS",
        "rubros_extra":  ["WORKSHOP"],
        "tagline":       "Casa de repuestos con taller propio",
        "with_desarme":  False,
        "with_repuestos": True,
    },
    {
        "slot":          "06",
        "username":      "vc_carwash",
        "display":       "Demo Carwash",
        "nombre_taller": "Demo AutoSpa Detailing",
        "rubro":         "DETAILING",
        "rubros_extra":  [],
        "tagline":       "Lavado y detailing profesional",
        "with_desarme":  False,
        "with_repuestos": False,
    },
    {
        "slot":          "07",
        "username":      "vc_vulcanizacion",
        "display":       "Demo Vulcanización",
        "nombre_taller": "Demo Neumáticos y Llantas",
        "rubro":         "TIRE",
        "rubros_extra":  [],
        "tagline":       "Vulcanización y alineación",
        "with_desarme":  False,
        "with_repuestos": True,
    },
    {
        "slot":          "08",
        "username":      "vc_escapes",
        "display":       "Demo Escapes",
        "nombre_taller": "Demo Escapes y Tubos",
        "rubro":         "EXHAUST",
        "rubros_extra":  [],
        "tagline":       "Especialistas en escapes y sistemas de escape",
        "with_desarme":  False,
        "with_repuestos": True,
    },
    {
        "slot":          "09",
        "username":      "vc_flotas",
        "display":       "Demo Mantención Flotas",
        "nombre_taller": "Demo FlotasService",
        "rubro":         "FLEET",
        "rubros_extra":  [],
        "tagline":       "Mantención preventiva para flotas corporativas",
        "with_desarme":  False,
        "with_repuestos": True,
    },
    {
        "slot":          "10",
        "username":      "vc_enterprise",
        "display":       "Demo Full Enterprise",
        "nombre_taller": "Demo AutoCenter Enterprise",
        "rubro":         "MIXED",
        "rubros_extra":  ["WORKSHOP", "PARTS", "DESARMADURIA"],
        "tagline":       "Centro automotriz completo — todos los módulos activos",
        "with_desarme":  True,
        "with_repuestos": True,
    },
]

CLIENTES_BASE = [
    {"nombre": "Pedro",    "apellido": "González",  "telefono": "+56 9 1111 0001"},
    {"nombre": "María",    "apellido": "Rojas",     "telefono": "+56 9 1111 0002"},
    {"nombre": "Empresa",  "apellido": "Demo SpA",  "telefono": "+56 9 1111 0003", "giro": "Comercio automotriz"},
]

REPUESTOS_BASE = [
    {"part_number": "VC-FIL-001", "nombre": "Filtro de aceite",   "precio_compra": Decimal("3500"),  "precio_venta": Decimal("5500"),  "cantidad_stock": 20},
    {"part_number": "VC-FIL-002", "nombre": "Filtro de aire",     "precio_compra": Decimal("4200"),  "precio_venta": Decimal("6800"),  "cantidad_stock": 15},
    {"part_number": "VC-BUJ-001", "nombre": "Bujías (set x4)",    "precio_compra": Decimal("6000"),  "precio_venta": Decimal("9500"),  "cantidad_stock": 12},
    {"part_number": "VC-ACE-001", "nombre": "Aceite motor 5W-30", "precio_compra": Decimal("8500"),  "precio_venta": Decimal("13000"), "cantidad_stock": 30},
    {"part_number": "VC-PAD-001", "nombre": "Pastillas de freno", "precio_compra": Decimal("12000"), "precio_venta": Decimal("19000"), "cantidad_stock": 8},
    {"part_number": "VC-COR-001", "nombre": "Correa de distribución", "precio_compra": Decimal("18000"), "precio_venta": Decimal("28000"), "cantidad_stock": 5},
]

DESARME_VEHICULOS = [
    {"marca": "Toyota",  "modelo": "Corolla", "anio": 2008, "patente": "VC-DES-001", "ubicacion": "Patio A-01"},
    {"marca": "Chevrolet", "modelo": "Spark", "anio": 2010, "patente": "VC-DES-002", "ubicacion": "Patio A-02"},
    {"marca": "Hyundai", "modelo": "Accent",  "anio": 2006, "patente": "VC-DES-003", "ubicacion": "Patio B-01"},
]


class Command(BaseCommand):
    help = "Creates/updates the eGarage Validation Center (10 demo companies)"

    def add_arguments(self, parser):
        parser.add_argument("--list",  action="store_true", help="Show credentials table without creating data")
        parser.add_argument("--reset", action="store_true", help="Delete vc_* users and companies before recreating")

    def handle(self, *args, **options):
        if options["list"]:
            self._print_table()
            return

        if options["reset"]:
            self._reset()

        User = get_user_model()
        created_count = 0
        updated_count = 0

        for profile in PROFILES:
            self.stdout.write(
                self.style.MIGRATE_HEADING(
                    f"\n[{profile['slot']}] {profile['display']} ({profile['rubro']})"
                )
            )
            with transaction.atomic():
                result = self._bootstrap_profile(User, profile)
                if result == "created":
                    created_count += 1
                else:
                    updated_count += 1

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"Validation Center listo. Nuevas: {created_count} | Actualizadas: {updated_count}"
        ))
        self._print_table()

    # ------------------------------------------------------------------
    # Bootstrap one profile
    # ------------------------------------------------------------------

    def _bootstrap_profile(self, User, profile: dict) -> str:
        username = profile["username"]
        email = f"{username}@demo.egarage.cl"

        user, user_created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "is_staff": False,
                "is_superuser": False,
                "is_active": True,
            },
        )
        if user_created:
            user.set_password(VC_PASSWORD)
            user.save(update_fields=["password"])
        self.stdout.write(f"  usuario: {username} (nuevo={user_created})")

        empresa_fields = {
            "nombre_taller": profile["nombre_taller"],
            "empresa": profile["nombre_taller"],
            "pais": "CL",
            "email": email,
            "telefono": f"+56 2 2222 {profile['slot']}00",
            "plan": PLAN_GROWTH,
            "suscripcion_activa": True,
            "zona_horaria": "America/Santiago",
        }
        empresa, empresa_created = Empresa.objects.get_or_create(
            user=user,
            defaults=self._safe_fields(Empresa, empresa_fields),
        )
        if not empresa_created:
            for k, v in self._safe_fields(Empresa, {"nombre_taller": profile["nombre_taller"]}).items():
                setattr(empresa, k, v)
            empresa.save(update_fields=["nombre_taller"])
        self.stdout.write(f"  empresa: {empresa.nombre_taller} (nueva={empresa_created})")

        config, _ = ConfiguracionEmpresa.objects.get_or_create(empresa=empresa)
        config.rubro_principal = profile["rubro"]
        config.rubros = profile["rubros_extra"]
        config.nombre_publico = profile["nombre_taller"]
        config.tagline = profile["tagline"]
        config.modules_configured_at = config.modules_configured_at or timezone.now()
        config.save(update_fields=[
            "rubro_principal", "rubros", "nombre_publico", "tagline", "modules_configured_at"
        ])
        self.stdout.write(f"  config: rubro={profile['rubro']} rubros_extra={profile['rubros_extra']}")

        self._seed_clientes(empresa)

        if profile["with_repuestos"]:
            self._seed_repuestos(empresa)

        if profile["with_desarme"]:
            self._seed_desarme(empresa)

        return "created" if empresa_created else "updated"

    # ------------------------------------------------------------------
    # Seed helpers
    # ------------------------------------------------------------------

    def _seed_clientes(self, empresa):
        for i, data in enumerate(CLIENTES_BASE):
            slug = empresa.user.username.replace("vc_", "")
            telefono = data["telefono"][:-4] + f"{i+1:04d}"
            lookup = {"empresa": empresa, "telefono": telefono}
            defaults = {
                "nombre": data["nombre"],
                "apellido": data.get("apellido", ""),
                "giro": data.get("giro", ""),
                **lookup,
            }
            cliente, created = Cliente.objects.get_or_create(**lookup, defaults=self._safe_fields(Cliente, defaults))
            if created:
                self.stdout.write(f"  cliente: {cliente} (nuevo)")

    def _seed_repuestos(self, empresa):
        for data in REPUESTOS_BASE:
            lookup = {"empresa": empresa, "part_number": data["part_number"]}
            defaults = {**data, "empresa": empresa}
            repuesto, created = Repuesto.objects.get_or_create(
                **lookup,
                defaults=self._safe_fields(Repuesto, defaults),
            )
            if created:
                self.stdout.write(f"  repuesto: {repuesto.nombre} (nuevo)")

    def _seed_desarme(self, empresa):
        for veh in DESARME_VEHICULOS:
            patente = f"{empresa.user.username[:4].upper()}-{veh['patente']}"
            lookup = {"empresa": empresa, "patente": patente}
            defaults = {
                "empresa": empresa,
                "marca_texto": veh["marca"],
                "modelo_texto": veh["modelo"],
                "anio": veh["anio"],
                "patente": patente,
                "estado_desarme": "INGRESADO",
                "ubicacion_fisica": veh["ubicacion"],
            }
            vd, created = VehiculoDesarme.objects.get_or_create(
                **lookup,
                defaults=self._safe_fields(VehiculoDesarme, defaults),
            )
            if created:
                self.stdout.write(f"  vehiculo desarme: {vd} (nuevo)")

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def _safe_fields(self, model, data: dict) -> dict:
        allowed = {f.name for f in model._meta.get_fields()}
        return {k: v for k, v in data.items() if k in allowed}

    def _reset(self):
        User = get_user_model()
        usernames = [p["username"] for p in PROFILES]
        deleted_users = User.objects.filter(username__in=usernames).count()
        User.objects.filter(username__in=usernames).delete()
        self.stdout.write(self.style.WARNING(f"Reset: {deleted_users} usuarios y sus empresas eliminados."))

    def _print_table(self):
        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("── eGarage Validation Center ──────────────────────────────"))
        self.stdout.write(f"{'#':<4} {'Usuario':<22} {'Contraseña':<10} {'Rubro':<16} {'Rubros extra'}")
        self.stdout.write("─" * 72)
        for p in PROFILES:
            extras = "+".join(p["rubros_extra"]) if p["rubros_extra"] else "—"
            self.stdout.write(
                f"{p['slot']:<4} {p['username']:<22} {VC_PASSWORD:<10} {p['rubro']:<16} {extras}"
            )
        self.stdout.write("─" * 72)
        self.stdout.write(f"URL local:  http://127.0.0.1:8000/cl/es/dashboard/")
        self.stdout.write(f"URL prod:   https://app.egarage.cl/cl/es/dashboard/")
        self.stdout.write("")

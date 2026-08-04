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

import struct
import zlib
from datetime import date, timedelta
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
from taller.models.lineas_documento import LineaRepuesto, ORIGEN_EXTERNO
from taller.models.pieza_desarme import PiezaDesarme
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
    {"marca": "Toyota",    "modelo": "Corolla", "anio": 2008, "patente": "VC-DES-001", "ubicacion": "Patio A-01"},
    {"marca": "Chevrolet", "modelo": "Spark",   "anio": 2010, "patente": "VC-DES-002", "ubicacion": "Patio A-02"},
    {"marca": "Hyundai",   "modelo": "Accent",  "anio": 2006, "patente": "VC-DES-003", "ubicacion": "Patio B-01"},
]

# Agotados — alimentan WGT_KPI_DESARM_DEPLETED
DESARME_VEHICULOS_AGOTADOS = [
    {"marca": "Nissan", "modelo": "Tiida",   "anio": 2005, "patente": "VC-AGT-001", "ubicacion": "Patio C-01"},
    {"marca": "Kia",    "modelo": "Picanto", "anio": 2007, "patente": "VC-AGT-002", "ubicacion": "Patio C-02"},
]

# Documentos — alimentan activity_feed y WGT_KPI_PARTS_SOLD_TODAY
DOCUMENTOS_DEMO = [
    {
        "tipo": "OT",
        "lineas": [
            ("SRV-DX",     "Diagnóstico electrónico", 1, Decimal("15000")),
            ("VC-BUJ-001", "Bujías (set x4)",         1, Decimal("9500")),
        ],
    },
    {
        "tipo": "PTS",
        "lineas": [
            ("VC-FIL-001", "Filtro de aceite",    3, Decimal("5500")),
            ("VC-ACE-001", "Aceite motor 5W-30",  2, Decimal("13000")),
        ],
    },
    {
        "tipo": "FAC",
        "lineas": [
            ("VC-PAD-001", "Pastillas de freno",  1, Decimal("19000")),
        ],
    },
]


# Ruta relativa (dentro de MEDIA_ROOT) del PNG de 1×1 px que usan las piezas demo sanas.
PLACEHOLDER_IMAGEN = "piezas_desarme/placeholder_vc.png"

# Vehículos atascados: alimentan alrt_desarm_delayed (> 30 días sin avanzar)
DESARME_VEHICULOS_STUCK = [
    {"patente": "VC-STK-001", "marca": "Ford",    "modelo": "Fiesta", "anio": 2007, "estado": "INGRESADO"},
    {"patente": "VC-STK-002", "marca": "Renault", "modelo": "Clio",   "anio": 2009, "estado": "DESARMANDO"},
]

# Piezas con problemas operativos: alimentan las 3 alertas de PiezaDesarme.
# "" en imagen  → sin foto (coincide con Q(imagen="") | Q(imagen__isnull=True)).
# PLACEHOLDER_IMAGEN → archivo real en MEDIA_ROOT; no dispara ninguna alerta.
DESARME_ALERT_PIEZAS = [
    # sin_foto × 3  (imagen vacía, precio OK, ubicación OK)
    {"codigo": "VC-ALT-FTO-001", "nombre": "Alternador sin foto",       "imagen": "",               "precio_venta_sugerido": Decimal("45000"),  "precio_sugerido": None, "ubicacion_fisica": "Zona-A1"},
    {"codigo": "VC-ALT-FTO-002", "nombre": "Arranque sin foto",         "imagen": "",               "precio_venta_sugerido": Decimal("32000"),  "precio_sugerido": None, "ubicacion_fisica": "Zona-A2"},
    {"codigo": "VC-ALT-FTO-003", "nombre": "Caja de cambios sin foto",  "imagen": "",               "precio_venta_sugerido": Decimal("120000"), "precio_sugerido": None, "ubicacion_fisica": "Zona-B1"},
    # sin_precio × 2  (imagen placeholder, ambos precios None, ubicación OK)
    {"codigo": "VC-ALT-PRC-001", "nombre": "Radiador sin precio",       "imagen": PLACEHOLDER_IMAGEN, "precio_venta_sugerido": None, "precio_sugerido": None, "ubicacion_fisica": "Zona-C1"},
    {"codigo": "VC-ALT-PRC-002", "nombre": "Compresor A/C sin precio",  "imagen": PLACEHOLDER_IMAGEN, "precio_venta_sugerido": None, "precio_sugerido": None, "ubicacion_fisica": "Zona-C2"},
    # sin_ubicacion × 4  (imagen placeholder, precio OK, ubicacion_fisica=None)
    {"codigo": "VC-ALT-UBI-001", "nombre": "Guardabarro delantero",          "imagen": PLACEHOLDER_IMAGEN, "precio_venta_sugerido": Decimal("18000"),  "precio_sugerido": None, "ubicacion_fisica": None},
    {"codigo": "VC-ALT-UBI-002", "nombre": "Puerta delantera izquierda",     "imagen": PLACEHOLDER_IMAGEN, "precio_venta_sugerido": Decimal("25000"),  "precio_sugerido": None, "ubicacion_fisica": None},
    {"codigo": "VC-ALT-UBI-003", "nombre": "Faro derecho",                   "imagen": PLACEHOLDER_IMAGEN, "precio_venta_sugerido": Decimal("15000"),  "precio_sugerido": None, "ubicacion_fisica": None},
    {"codigo": "VC-ALT-UBI-004", "nombre": "Parabrisas trasero",             "imagen": PLACEHOLDER_IMAGEN, "precio_venta_sugerido": Decimal("35000"),  "precio_sugerido": None, "ubicacion_fisica": None},
    # Piezas sanas (no deben disparar ninguna alerta)
    {"codigo": "VC-OK-001", "nombre": "Motor completo",           "imagen": PLACEHOLDER_IMAGEN, "precio_venta_sugerido": Decimal("250000"), "precio_sugerido": None, "ubicacion_fisica": "Motor-01"},
    {"codigo": "VC-OK-002", "nombre": "Transmisión automática",   "imagen": PLACEHOLDER_IMAGEN, "precio_venta_sugerido": Decimal("180000"), "precio_sugerido": None, "ubicacion_fisica": "Trans-01"},
]


def _make_minimal_png() -> bytes:
    """Genera un PNG válido de 1×1 px en escala de grises (sin Pillow)."""
    sig = b"\x89PNG\r\n\x1a\n"

    def chunk(tag: bytes, data: bytes) -> bytes:
        c = tag + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 0, 0, 0, 0))
    idat = chunk(b"IDAT", zlib.compress(b"\x00\x80", 9))
    iend = chunk(b"IEND", b"")
    return sig + ihdr + idat + iend


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
        self._seed_email_address(user)

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
            self._seed_alert_data(empresa)

        self._seed_documentos_emitidos(empresa)

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

        for veh in DESARME_VEHICULOS_AGOTADOS:
            patente = f"{empresa.user.username[:4].upper()}-{veh['patente']}"
            lookup = {"empresa": empresa, "patente": patente}
            defaults = {
                "empresa": empresa,
                "marca_texto": veh["marca"],
                "modelo_texto": veh["modelo"],
                "anio": veh["anio"],
                "patente": patente,
                "estado_desarme": "AGOTADO",
                "ubicacion_fisica": veh["ubicacion"],
            }
            vd, created = VehiculoDesarme.objects.get_or_create(
                **lookup,
                defaults=self._safe_fields(VehiculoDesarme, defaults),
            )
            if created:
                self.stdout.write(f"  vehiculo agotado: {vd} (nuevo)")

    def _ensure_placeholder_image(self) -> str:
        """Crea MEDIA_ROOT/piezas_desarme/placeholder_vc.png si no existe. Devuelve la ruta relativa."""
        from pathlib import Path
        from django.conf import settings

        path = Path(getattr(settings, "MEDIA_ROOT", "media")) / PLACEHOLDER_IMAGEN
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(_make_minimal_png())
            self.stdout.write(f"  placeholder imagen: {PLACEHOLDER_IMAGEN} (creado)")
        return PLACEHOLDER_IMAGEN

    def _ensure_fields(self, obj, expected: dict) -> list[str]:
        """
        Compara los campos de obj contra expected y actualiza si difieren.
        ImageField se compara por .name (ruta almacenada), normalizado a "".
        Devuelve la lista de campos modificados.
        """
        update = {}
        for k, v in expected.items():
            current = getattr(obj, k, None)
            if hasattr(current, "name"):       # FieldFile / ImageField
                current = current.name or ""
            if current != v:
                update[k] = v
        if update:
            for k, v in update.items():
                setattr(obj, k, v)
            obj.save(update_fields=list(update.keys()))
        return list(update.keys())

    def _seed_alert_data(self, empresa):
        """Siembra y restaura idempotentemente los datos de las 4 alertas de DESARMADURIA."""
        today = date.today()
        stuck_date = today - timedelta(days=45)
        cutoff = today - timedelta(days=30)
        placeholder_path = self._ensure_placeholder_image()

        # ── Vehículos atascados ──────────────────────────────────────────
        for sv in DESARME_VEHICULOS_STUCK:
            patente = f"{empresa.user.username[:4].upper()}-{sv['patente']}"
            vd, created = VehiculoDesarme.objects.get_or_create(
                empresa=empresa,
                patente=patente,
                defaults=self._safe_fields(VehiculoDesarme, {
                    "empresa": empresa,
                    "patente": patente,
                    "marca_texto": sv["marca"],
                    "modelo_texto": sv["modelo"],
                    "anio": sv["anio"],
                    "estado_desarme": sv["estado"],
                    "fecha_ingreso_desarme": stuck_date,
                    "es_placeholder": False,
                }),
            )
            if created:
                self.stdout.write(f"  vehiculo atascado: {patente} (nuevo)")
            else:
                expected = {"estado_desarme": sv["estado"], "es_placeholder": False}
                # Restaurar fecha si está ausente o ya no dispararía la alerta
                if vd.fecha_ingreso_desarme is None or vd.fecha_ingreso_desarme >= cutoff:
                    expected["fecha_ingreso_desarme"] = stuck_date
                changed = self._ensure_fields(vd, expected)
                if changed:
                    self.stdout.write(f"  vehiculo atascado: {patente} (restaurado: {changed})")

        # ── Carrier para piezas: primer vehículo activo de la empresa ───
        carrier = VehiculoDesarme.objects.filter(
            empresa=empresa,
            estado_desarme__in=["INGRESADO", "DESARMANDO"],
            es_placeholder=False,
        ).first()
        if carrier is None:
            carrier_patente = f"{empresa.user.username[:4].upper()}-VC-CARR-001"
            carrier, _ = VehiculoDesarme.objects.get_or_create(
                empresa=empresa,
                patente=carrier_patente,
                defaults=self._safe_fields(VehiculoDesarme, {
                    "empresa": empresa,
                    "patente": carrier_patente,
                    "marca_texto": "Toyota",
                    "modelo_texto": "Corolla",
                    "anio": 2010,
                    "estado_desarme": "INGRESADO",
                    "es_placeholder": False,
                }),
            )

        # ── Piezas de alerta ────────────────────────────────────────────
        for pd in DESARME_ALERT_PIEZAS:
            img = placeholder_path if pd["imagen"] == PLACEHOLDER_IMAGEN else pd["imagen"]
            pieza_fields = {
                "nombre":                pd["nombre"],
                "imagen":                img,
                "precio_venta_sugerido": pd["precio_venta_sugerido"],
                "precio_sugerido":       pd["precio_sugerido"],
                "ubicacion_fisica":      pd["ubicacion_fisica"],
                "estado_pieza":          "DISPONIBLE",
                "activo":                True,
            }
            pieza, created = PiezaDesarme.objects.get_or_create(
                empresa=empresa,
                vehiculo_desarme=carrier,
                codigo=pd["codigo"],
                defaults=self._safe_fields(PiezaDesarme, {
                    **pieza_fields,
                    "empresa": empresa,
                    "vehiculo_desarme": carrier,
                    "codigo": pd["codigo"],
                }),
            )
            if created:
                self.stdout.write(f"  pieza alerta: {pd['codigo']} (nueva)")
            else:
                changed = self._ensure_fields(pieza, self._safe_fields(PiezaDesarme, pieza_fields))
                if changed:
                    self.stdout.write(f"  pieza alerta: {pd['codigo']} (restaurada: {changed})")

    def _seed_email_address(self, user):
        """Crea o actualiza el EmailAddress de Allauth como verified+primary."""
        try:
            from allauth.account.models import EmailAddress
        except ImportError:
            return
        EmailAddress.objects.update_or_create(
            user=user,
            email=user.email,
            defaults={"verified": True, "primary": True},
        )

    def _seed_documentos_emitidos(self, empresa):
        today = timezone.now().date()

        cliente = Cliente.objects.filter(empresa=empresa).first()
        if not cliente:
            return

        for demo in DOCUMENTOS_DEMO:
            tipo = demo["tipo"]
            if Documento.objects.filter(
                empresa=empresa,
                tipo=tipo,
                estado="EMITIDO",
                fecha_emision=today,
            ).exists():
                continue

            doc = Documento.objects.create(
                empresa=empresa,
                cliente=cliente,
                tipo=tipo,
                estado="EMITIDO",
                fecha_emision=today,
            )
            for codigo, nombre, cantidad, precio in demo["lineas"]:
                LineaRepuesto.objects.create(
                    documento=doc,
                    codigo=codigo,
                    nombre=nombre,
                    cantidad=cantidad,
                    precio_unitario=precio,
                    origen_repuesto=ORIGEN_EXTERNO,
                )
            doc.save()  # triggers recompute_totals after lines exist
            self.stdout.write(f"  documento {tipo}: #{doc.numero} (nuevo)")

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def _safe_fields(self, model, data: dict) -> dict:
        allowed = {f.name for f in model._meta.get_fields()}
        return {k: v for k, v in data.items() if k in allowed}

    def _reset(self):
        """
        Elimina los vc_* usuarios y toda su data asociada en el orden correcto.

        PiezaDesarme usa on_delete=PROTECT sobre VehiculoDesarme, por lo que
        el cascade directo desde User falla.  Se limpian los modelos protegidos
        antes de eliminar la raíz.
        """
        from taller.models.lineas_documento import LineaRepuesto
        from taller.models.pieza_desarme import PiezaDesarme
        from taller.models.repuesto import Repuesto

        User = get_user_model()
        usernames = [p["username"] for p in PROFILES]
        empresas = Empresa.objects.filter(user__username__in=usernames)

        # Eliminar en orden inverso de dependencias protegidas
        PiezaDesarme.objects.filter(empresa__in=empresas).delete()
        VehiculoDesarme.objects.filter(empresa__in=empresas).delete()
        LineaRepuesto.objects.filter(documento__empresa__in=empresas).delete()
        Documento.objects.filter(empresa__in=empresas).delete()
        Cliente.objects.filter(empresa__in=empresas).delete()
        Repuesto.objects.filter(empresa__in=empresas).delete()

        deleted_users = User.objects.filter(username__in=usernames).count()
        User.objects.filter(username__in=usernames).delete()  # cascade: Empresa, Config, etc.
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

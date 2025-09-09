import random
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.timezone import now

from taller.models import Documento, Empresa, Repuesto, Tecnico
from taller.models.clientes import Cliente
from taller.models.lineas_documento import (
    LineaOtroServicio,
    LineaRepuesto,
    LineaServicio,
)
from taller.models.marca import Marca
from taller.models.modelo import Modelo
from taller.models.vehiculos import Vehiculo

# Catálogo base de prueba (ajusta si quieres otros)
REPUESTOS = [
    ("OF", "Filtro de aceite", 9990),
    ("AF", "Filtro de aire", 12990),
    ("PLG", "Bujía", 6990),
    ("BRK", "Pastillas de freno", 35990),
    ("BAT", "Batería 60Ah", 89990),
    ("WIP", "Plumillas", 5990),
    ("COOL", "Coolant 1L", 6990),
    ("FS1", "Filtro de combustible", 11990),
    ("BLT", "Correa accesorios", 22990),
]

SERVICIOS = [
    ("ALIN", "Alineación", 25000),
    ("BAL", "Balanceo", 15000),
    ("SCAN", "Scanner OBDII", 20000),
    ("LAB", "Mano de obra general", 30000),
    ("ROT", "Rotación de neumáticos", 12000),
    ("BRKS", "Servicio de frenos", 45000),
]

OTROS = [
    ("Rectificado de discos", "Tercero SPA", 15000, 22000),
    ("Carga de A/C", "FrioCar Ltda", 18000, 28000),
    ("Alineación 3D externa", "AlinExt Inc", 20000, 32000),
    ("Pulido faros externo", "LuzPro", 10000, 18000),
]

DEFAULT_TYPES = ["PRES", "OT", "FAC"]  # Ajusta a tus choices reales si difieren


def get_company(country: str, name: str | None):
    if name:
        emp = Empresa.objects.filter(nombre_taller=name).first()
        if emp:
            return emp
    if country.upper() == "US":
        emp = Empresa.objects.filter(pais="US").order_by("id").first()
        if not emp:
            emp = Empresa.objects.create(
                nombre_taller="USA Test Garage", pais="US", moneda="USD"
            )
        return emp
    emp = Empresa.objects.filter(pais="CL").order_by("id").first()
    if not emp:
        emp = Empresa.objects.create(
            nombre_taller="Chile Demo", pais="CL", moneda="CLP"
        )
    return emp


def ensure_parts(emp):
    for pn, nombre, price in REPUESTOS:
        Repuesto.objects.get_or_create(
            empresa=emp,
            part_number=pn,
            defaults={"nombre": nombre, "precio_venta": Decimal(price)},
        )


def get_basics(emp):
    cli, _ = Cliente.objects.get_or_create(empresa=emp, nombre="Cliente Demo")

    # Crear marca y modelo si no existen (usan country en lugar de empresa)
    marca, _ = Marca.objects.get_or_create(country=emp.pais, nombre="Toyota")
    modelo, _ = Modelo.objects.get_or_create(
        country=emp.pais, marca=marca, nombre="Corolla"
    )

    # Vehículo: usa el primero si existe; si no, crea el mínimo posible
    veh = Vehiculo.objects.filter(empresa=emp).order_by("id").first()
    if not veh:
        veh_defaults = {
            "marca": marca,
            "modelo": modelo,
            "patente": "TEST123",
            "anio": 2020,
        }
        # Intenta setear odómetro para que la lista muestre algo aunque doc no tenga 'millas'
        for fld in ("millas", "kilometraje", "odometro"):
            if hasattr(Vehiculo, fld):
                veh_defaults[fld] = 60000
                break
        veh = Vehiculo.objects.create(
            empresa=emp, cliente=cli, vin="1FAFP404XWF123456", **veh_defaults
        )
    tec, _ = Tecnico.objects.get_or_create(empresa=emp, nombre="Tech Demo", activo=True)
    return cli, veh, tec


def recalc_totals(doc: Documento):
    rep_sub = Decimal("0")
    for lr in doc.lineas_repuesto.all():
        d = (lr.descuento or 0) / Decimal("100")
        rep_sub += lr.cantidad * lr.precio_unitario * (Decimal("1") - d)
    serv_sub = sum(
        [
            (
                ls.cantidad
                * ls.precio_unitario
                * (Decimal("1") - (ls.descuento or 0) / Decimal("100"))
            )
            for ls in doc.lineas_servicio.all()
        ],
        Decimal("0"),
    )
    otros_sub = sum(
        [(lo.precio_cliente * lo.cantidad) for lo in doc.lineas_otro_servicio.all()],
        Decimal("0"),
    )

    iva_rate = Decimal("0.00") if doc.empresa.pais == "US" else Decimal("0.19")
    tax_amount = (rep_sub * iva_rate).quantize(Decimal("0.01"))
    total = (rep_sub + serv_sub + otros_sub + tax_amount).quantize(Decimal("0.01"))

    # Persistir (ajusta nombres si difieren)
    doc.neto_repuestos = rep_sub
    doc.neto_servicios = serv_sub + otros_sub
    doc.tax_rate_applied = iva_rate * 100
    doc.tax_amount = tax_amount
    doc.total = total
    doc.save(
        update_fields=[
            "neto_repuestos",
            "neto_servicios",
            "tax_rate_applied",
            "tax_amount",
            "total",
        ]
    )


def add_lines(doc: Documento, tec: Tecnico, min_items=3):
    emp = doc.empresa
    # Repuestos (>=3)
    all_parts = list(
        Repuesto.objects.filter(empresa=emp).values_list(
            "id", "part_number", "nombre", "precio_venta"
        )
    )
    random.shuffle(all_parts)
    for pid, pn, nombre, pventa in all_parts[: max(3, min_items)]:
        LineaRepuesto.objects.create(
            documento=doc,
            repuesto_id=pid,
            nombre=nombre or pn,
            cantidad=Decimal("1"),
            precio_unitario=Decimal(pventa or 9990),
            descuento=Decimal("0"),
            # heredar técnico si aplica tu flag de empresa
        )
    # Servicios (>=3)
    random.shuffle(SERVICIOS)
    for code, nombre, precio in SERVICIOS[: max(3, min_items)]:
        LineaServicio.objects.create(
            documento=doc,
            codigo=code,
            nombre=nombre,
            cantidad=Decimal("1"),
            precio_unitario=Decimal(precio),
            descuento=Decimal("0"),
        )
    # Otros servicios (>=3)
    random.shuffle(OTROS)
    for nom, ext, costo, precio in OTROS[: max(3, min_items)]:
        LineaOtroServicio.objects.create(
            documento=doc,
            nombre_servicio=nom,
            empresa_externa=ext,
            cantidad=Decimal("1"),
            costo_interno=Decimal(costo),
            precio_cliente=Decimal(precio),
            ganancia=Decimal(precio) - Decimal(costo),
        )


class Command(BaseCommand):
    help = "Crea N documentos por tipo (3 tipos) con millas, ≥3 repuestos, ≥3 servicios y ≥3 otros servicios."

    def add_arguments(self, parser):
        parser.add_argument(
            "--empresa", type=str, default="", help="Nombre de empresa (opcional)"
        )
        parser.add_argument("--country", type=str, default="US", help="US o CL")
        parser.add_argument(
            "--per-type", type=int, default=10, help="Documentos por tipo (default 10)"
        )
        parser.add_argument(
            "--types",
            type=str,
            default=",".join(DEFAULT_TYPES),
            help="Tipos separados por coma (ej: PRES,OT,FAC)",
        )

    @transaction.atomic
    def handle(self, *args, **opts):
        country = opts["country"].upper()
        emp = get_company(country, opts.get("empresa") or None)
        ensure_parts(emp)
        cli, veh, tec = get_basics(emp)

        tipos = [t.strip() for t in (opts["types"] or "").split(",") if t.strip()]
        if not tipos:
            tipos = DEFAULT_TYPES

        total_creados = 0

        for tipo in tipos:
            for i in range(int(opts["per_type"])):
                fields = dict(
                    empresa=emp,
                    cliente=cli,
                    vehiculo=veh,
                    fecha_emision=now().date(),
                    estado="emitido",
                    tipo=tipo,
                    country=emp.pais,
                    moneda=emp.moneda,
                )
                # Millas en Documento si existe el campo
                if hasattr(Documento, "millas"):
                    fields["millas"] = 65000 + total_creados * 100  # creciente
                doc = Documento.objects.create(**fields)

                add_lines(doc, tec, min_items=3)
                recalc_totals(doc)
                total_creados += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Empresa: {emp.nombre_taller} ({emp.pais}) | Tipos: {tipos} | Creados: {total_creados}"
            )
        )

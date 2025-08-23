from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.timezone import now
from decimal import Decimal
import random

from taller.models import (
    Empresa, Cliente, Vehiculo, Tecnico, Repuesto,
    Documento, LineaRepuesto, LineaServicio, LineaOtroServicio
)

R_PARTS = [
    # part_number, nombre, precio_venta
    ("OF", "Filtro de aceite", 9990),
    ("AF", "Filtro de aire", 12990),
    ("PLG", "Bujía", 6990),
    ("BRK", "Pastillas de freno", 35990),
    ("BAT", "Batería 60Ah", 89990),
    ("WIP", "Plumillas", 5990),
    ("COOL", "Coolant 1L", 6990),
]

R_SERVS = [
    # codigo, nombre, precio
    ("ALIN", "Alineación", 25000),
    ("BAL", "Balanceo", 15000),
    ("SCAN", "Scanner OBDII", 20000),
    ("LAB", "Mano de obra general", 30000),
]

R_OTROS = [
    # nombre, empresa_externa, costo, precio
    ("Rectificado de discos", "Tercero SPA", 15000, 22000),
    ("A/C carga gas", "FrioCar Ltda", 18000, 28000),
]

def get_or_create_us_company():
    emp = Empresa.objects.filter(country="US").order_by("id").first()
    if not emp:
        emp = Empresa.objects.create(nombre="USA Test Garage", country="US", moneda="USD")
    return emp

def seed_parts(emp):
    # Crea repuestos base si no existen
    for pn, nombre, price in R_PARTS:
        Repuesto.objects.get_or_create(
            empresa=emp, part_number=pn,
            defaults={"nombre": nombre, "precio_venta": Decimal(price)}
        )

def get_or_create_basics(emp):
    cli, _ = Cliente.objects.get_or_create(
        empresa=emp, nombre="Cliente Demo",
        defaults={"apellido": "Test", "email": "demo@test.com"}
    )
    
    # Necesitamos obtener marca y modelo existentes o crear básicos
    from taller.models import Marca, Modelo
    marca, _ = Marca.objects.get_or_create(
        empresa=emp, nombre="Toyota",
        defaults={"activo": True}
    )
    modelo, _ = Modelo.objects.get_or_create(
        marca=marca, nombre="Corolla",
        defaults={"activo": True}
    )
    
    veh, _ = Vehiculo.objects.get_or_create(
        empresa=emp, cliente=cli, vin="1FAFP404XWF123456",
        defaults={
            "marca": marca, 
            "modelo": modelo,
            "patente": "DEMO123",
            "anio": 2020
        }
    )
    tec, _ = Tecnico.objects.get_or_create(
        empresa=emp, nombre="Tech Demo", 
        defaults={"activo": True}
    )
    return cli, veh, tec

def recalc_totals(doc):
    from decimal import Decimal
    rep_sub = Decimal("0")
    for lr in doc.lineas_repuesto.all():
        d = (lr.descuento or 0) / Decimal("100")
        rep_sub += (lr.cantidad * lr.precio_unitario * (Decimal("1") - d))
    serv_sub = sum([ls.cantidad * ls.precio_unitario * (Decimal("1") - (ls.descuento or 0)/Decimal("100"))
                   for ls in doc.lineas_servicio.all()], Decimal("0"))
    otros_sub = sum([lo.precio_cliente * lo.cantidad for lo in doc.lineas_otro_servicio.all()], Decimal("0"))
    # En USA, no aplicamos IVA (sales tax configuraciones aparte). Para Chile usar 19% sobre repuestos.
    iva_rate = Decimal("0.00") if doc.empresa.country == "US" else Decimal("0.19")
    tax_amount = (rep_sub * iva_rate).quantize(Decimal("0.01"))
    total = (rep_sub + serv_sub + otros_sub + tax_amount).quantize(Decimal("0.01"))

    # Persistir (ajusta nombres si tu modelo difiere)
    doc.neto_repuestos = rep_sub
    doc.neto_servicios = serv_sub + otros_sub
    doc.tax_rate_applied = (iva_rate * 100)
    doc.tax_amount = tax_amount
    doc.total = total
    doc.save(update_fields=["neto_repuestos","neto_servicios","tax_rate_applied","tax_amount","total"])

class Command(BaseCommand):
    help = "Borra TODOS los documentos (por empresa) y crea N documentos completos con millas, repuestos, servicios y otros."

    def add_arguments(self, parser):
        parser.add_argument("--empresa", type=str, default="", help="Nombre de empresa. Si no se pasa, toma la primera US.")
        parser.add_argument("--count", type=int, default=10, help="Cantidad de documentos nuevos a crear")
        parser.add_argument("--hard", action="store_true", help="Borrar TODO para esa empresa")
        parser.add_argument("--country", type=str, default="US", help="US o CL (afecta impuestos/millas)")

    @transaction.atomic
    def handle(self, *args, **opts):
        country = opts["country"].upper()
        emp = Empresa.objects.filter(nombre=opts["empresa"]).first() if opts["empresa"] else None
        if not emp:
            emp = get_or_create_us_company() if country == "US" else Empresa.objects.filter(country="CL").first() or Empresa.objects.create(nombre="Chile Demo", country="CL", moneda="CLP")

        seed_parts(emp)
        cli, veh, tec = get_or_create_basics(emp)

        if opts["hard"]:
            # Borrar documentos + líneas para esa empresa
            # (FK cascada debe eliminar las líneas)
            Documento.objects.filter(empresa=emp).delete()

        created = 0
        for i in range(opts["count"]):
            doc = Documento.objects.create(
                empresa=emp,
                cliente=cli,
                vehiculo=veh,
                tecnico_responsable=tec,
                fecha_emision=now().date(),
                estado="EMITIDO",  # Usar valores válidos del modelo
                tipo="PRES" if i % 2 == 0 else "OT",  # PRES o OT según el modelo
                country=country,
                moneda="USD" if country == "US" else "CLP",
                **({"millas": 65000 + i*500} if hasattr(Documento, "millas") else {})
            )

            # >=3 repuestos
            parts = random.sample(R_PARTS, k=3)
            for pn, nombre, price in parts:
                rep = Repuesto.objects.filter(empresa=emp, part_number=pn).first()
                LineaRepuesto.objects.create(
                    documento=doc,
                    repuesto=rep,
                    nombre=nombre,
                    cantidad=Decimal("1"),
                    precio_unitario=Decimal(price),
                    descuento=Decimal("0")
                )

            # >=1 servicio
            s_code, s_name, s_price = random.choice(R_SERVS)
            LineaServicio.objects.create(
                documento=doc,
                codigo=s_code,
                nombre=s_name,
                cantidad=Decimal("1"),
                precio_unitario=Decimal(s_price),
                descuento=Decimal("0")
            )

            # >=1 otro servicio
            o_name, o_emp, o_cost, o_price = random.choice(R_OTROS)
            LineaOtroServicio.objects.create(
                documento=doc,
                nombre=o_name,
                empresa_externa=o_emp,
                cantidad=Decimal("1"),
                costo_interno=Decimal(o_cost),
                precio_cliente=Decimal(o_price),
                ganancia=Decimal(o_price) - Decimal(o_cost)
            )

            recalc_totals(doc)
            created += 1

        self.stdout.write(self.style.SUCCESS(f"Empresa: {emp.nombre} ({emp.country})"))
        self.stdout.write(self.style.SUCCESS(f"Documentos creados: {created}"))

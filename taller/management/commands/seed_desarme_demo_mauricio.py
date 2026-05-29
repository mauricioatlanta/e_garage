from decimal import Decimal
import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model

from taller.models import (
    Cliente,
    Documento,
    Empresa,
    LineaRepuesto,
    PiezaDesarme,
    Repuesto,
    Vehiculo,
    VendedorDesarme,
)

RND = random.Random(20260516)

MARCAS_MODELOS = [
    ("Toyota", "Corolla"), ("Toyota", "Yaris"), ("Toyota", "Hilux"),
    ("Nissan", "Versa"), ("Nissan", "Sentra"), ("Nissan", "Navara"),
    ("Hyundai", "Accent"), ("Hyundai", "Elantra"), ("Hyundai", "Tucson"),
    ("Kia", "Rio"), ("Kia", "Morning"), ("Kia", "Sportage"),
    ("Chevrolet", "Sail"), ("Chevrolet", "Spark"), ("Chevrolet", "Captiva"),
    ("Suzuki", "Swift"), ("Suzuki", "Baleno"), ("Suzuki", "Vitara"),
    ("Mazda", "3"), ("Mazda", "CX-5"),
    ("Ford", "Ranger"), ("Ford", "Escape"),
]

PIEZAS = [
    ("MOTOR", "Motor completo", 650000, 1550000),
    ("CAJA", "Caja de cambios", 380000, 950000),
    ("ECU", "Computador ECU", 120000, 420000),
    ("ALTERNADOR", "Alternador", 65000, 180000),
    ("MOTORPARTIDA", "Motor de partida", 55000, 160000),
    ("TURBO", "Turbo", 180000, 650000),
    ("RADIADOR", "Radiador", 60000, 190000),
    ("OPTICO-D", "Óptico derecho", 45000, 180000),
    ("OPTICO-I", "Óptico izquierdo", 45000, 180000),
    ("FOCO-TD", "Foco trasero derecho", 35000, 140000),
    ("FOCO-TI", "Foco trasero izquierdo", 35000, 140000),
    ("PUERTA-D", "Puerta delantera derecha", 90000, 280000),
    ("PUERTA-I", "Puerta delantera izquierda", 90000, 280000),
    ("PARACHOQUE", "Parachoque delantero", 70000, 230000),
    ("CAPOT", "Capot", 85000, 260000),
    ("TAPA-MALETA", "Tapa maleta", 70000, 240000),
    ("LLANTA", "Llanta", 35000, 120000),
    ("AIRBAG", "Airbag conductor", 90000, 320000),
    ("TABLERO", "Tablero completo", 120000, 420000),
    ("INYECTOR", "Inyector", 45000, 180000),
]

NOMBRES_CLIENTES = [
    "Comercial Los Pinos", "Repuestos San Miguel", "Taller Express",
    "Automotora Central", "Mecánica Rápida", "ServiAuto Chile",
    "Repuestos Miraflores", "Taller El Bosque", "Grúas Valparaíso",
    "Lubricentro Andes",
]


def cl_patente(n):
    letters = "BCDFGHJKLMNPRSTVWXYZ"
    return f"{letters[n % len(letters)]}{letters[(n//2) % len(letters)]}{letters[(n//3) % len(letters)]}{letters[(n//5) % len(letters)]}{n%10}{(n//10)%10}"


def get_or_none(model, **kwargs):
    return model.objects.filter(**kwargs).first()


class Command(BaseCommand):
    help = "Puebla desarme con vehículos, piezas y ventas demo para mauricioatlanta@gmail.com / empresa 2."

    def add_arguments(self, parser):
        parser.add_argument("--email", default="mauricioatlanta@gmail.com")
        parser.add_argument("--vehiculos", type=int, default=35)
        parser.add_argument("--ventas", type=int, default=90)
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **opts):
        User = get_user_model()
        user = User.objects.select_related("empresa").get(email=opts["email"])
        empresa = user.empresa or Empresa.objects.get(id=2)

        self.stdout.write(f"EMPRESA_ID={empresa.id} EMPRESA={empresa.nombre} EMAIL={user.email}")

        if opts["dry_run"]:
            self.stdout.write("DRY_RUN_OK")
            return

        clientes = []
        for i, nombre in enumerate(NOMBRES_CLIENTES, start=1):
            c, _ = Cliente.objects.get_or_create(
                empresa=empresa,
                nombre=f"{nombre} DEMO DESARME",
                defaults={
                    "email": f"cliente.desarme.{i}@demo.local",
                    "telefono": f"+56955{i:06d}",
                },
            )
            clientes.append(c)

        vendedores = []
        for i in range(1, 8):
            v, _ = VendedorDesarme.objects.get_or_create(
                empresa=empresa,
                nombre=f"Proveedor Desarme Demo {i}",
                defaults={
                    "telefono": f"+56988{i:06d}",
                    "email": f"proveedor.desarme.{i}@demo.local",
                    "direccion": f"Calle Demo {100+i}",
                    "lugar_compra": "Chile",
                },
            )
            vendedores.append(v)

        vehiculos = []
        for i in range(1, opts["vehiculos"] + 1):
            marca, modelo = RND.choice(MARCAS_MODELOS)
            anio = RND.randint(2008, 2021)
            patente = cl_patente(7000 + i)

            veh, _ = Vehiculo.objects.get_or_create(
                empresa=empresa,
                patente=patente,
                defaults={
                    "cliente": clientes[0],
                    "tipo_uso": "DESARME",
                    "marca_texto": marca,
                    "modelo_texto": modelo,
                    "anio": anio,
                    "precio_compra": Decimal(RND.randrange(850000, 5200000, 50000)),
                    "fecha_ingreso_desarme": date.today() - timedelta(days=RND.randint(5, 240)),
                    "estado_desarme": RND.choice(["INGRESADO", "EN_DESARME", "DESARMADO"]),
                    "ubicacion_fisica": f"Patio {RND.randint(1,5)} / Fila {RND.randint(1,12)}",
                    "observaciones_desarme": "Vehículo demo para análisis de rentabilidad.",
                    "vendedor_desarme": RND.choice(vendedores),
                    "lugar_compra": "Compra demo",
                },
            )
            vehiculos.append(veh)

            for idx, (codigo_base, nombre_pieza, pmin, pmax) in enumerate(RND.sample(PIEZAS, k=RND.randint(10, 16)), start=1):
                precio = Decimal(RND.randrange(pmin, pmax, 5000))
                costo = (precio * Decimal("0.38")).quantize(Decimal("1"))
                PiezaDesarme.objects.get_or_create(
                    empresa=empresa,
                    vehiculo=veh,
                    codigo=f"D-{veh.id}-{codigo_base}",
                    defaults={
                        "nombre": f"{nombre_pieza} {marca} {modelo} {anio}",
                        "cantidad": RND.choice([1, 1, 1, 2]),
                        "costo_asignado": costo,
                        "precio_venta_sugerido": precio,
                        "precio_referencia": precio,
                        "precio_sugerido": precio,
                        "origen_precio": "DEMO",
                        "prioridad": RND.randint(1, 5),
                        "revisado": True,
                        "fecha_extraccion": date.today() - timedelta(days=RND.randint(1, 180)),
                        "activo": True,
                        "estado_pieza": "DISPONIBLE",
                        "ubicacion_fisica": f"Bodega D{RND.randint(1,4)}-{RND.randint(10,99)}",
                    },
                )

        piezas_qs = PiezaDesarme.objects.filter(empresa=empresa, activo=True, cantidad__gt=0).order_by("?")
        ventas_creadas = 0

        for i in range(1, opts["ventas"] + 1):
            pieza = piezas_qs.first()
            if not pieza:
                break

            cliente = RND.choice(clientes)
            fecha = date.today() - timedelta(days=RND.randint(0, 150))
            precio = pieza.precio_sugerido or pieza.precio_venta_sugerido or pieza.precio_referencia or Decimal("50000")
            cantidad = 1
            total = precio * cantidad

            doc = Documento.objects.create(
                empresa=empresa,
                tipo="PTS",
                estado="EMITIDO",
                fecha_emision=fecha,
                cliente=cliente,
                vehiculo=None,
                moneda=getattr(empresa, "moneda", "CLP") or "CLP",
                country=getattr(empresa, "pais", "CL") or "CL",
                neto_repuestos=total,
                neto_servicios=Decimal("0"),
                neto_otros_servicios=Decimal("0"),
                tax_rate_applied=Decimal("0"),
                tax_amount=Decimal("0"),
                total=total,
                legacy_total_repuestos=total,
                legacy_total_general=total,
                payment_status="PAID",
                estado_pago="PAGADO",
                pagado=True,
                monto_pagado=total,
                saldo_pendiente=Decimal("0"),
                observaciones=f"Venta demo desarme pieza {pieza.codigo}",
            )

            LineaRepuesto.objects.create(
                documento=doc,
                repuesto=None,
                codigo=pieza.codigo,
                nombre=pieza.nombre,
                cantidad=cantidad,
                precio_unitario=precio,
                descuento=Decimal("0"),
                origen_repuesto="DESARME",
                pieza_desarme=pieza,
                costo_linea=pieza.costo_asignado,
            )

            pieza.cantidad = max(0, pieza.cantidad - cantidad)
            if pieza.cantidad == 0:
                pieza.activo = False
                pieza.estado_pieza = "VENDIDA"
            pieza.save(update_fields=["cantidad", "activo", "estado_pieza", "updated_at"])

            ventas_creadas += 1

        self.stdout.write(self.style.SUCCESS(f"OK vehiculos={len(vehiculos)} piezas={PiezaDesarme.objects.filter(empresa=empresa).count()} ventas_creadas={ventas_creadas}"))

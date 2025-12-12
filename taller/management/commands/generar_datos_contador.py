"""
Comando para generar datos de prueba para el módulo de Contador Virtual.
Crea clientes, vehículos, documentos (facturas, órdenes de trabajo, presupuestos)
con repuestos, servicios y otros servicios.
"""

import random
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from taller.models.clientes import Cliente
from taller.models.documento import Documento
from taller.models.empresa import Empresa
from taller.models.lineas_documento import (
    LineaOtroServicio,
    LineaRepuesto,
    LineaServicio,
)
from taller.models.repuesto import Repuesto
from taller.models.tecnico import Tecnico
from taller.models.vehiculos import Vehiculo
from taller.servicios.models import CategoriaServicio, Servicio, SubcategoriaServicio


class Command(BaseCommand):
    help = "Genera datos de prueba para el módulo Contador Virtual: 30 clientes, vehículos, 20 facturas, 20 OTs, 10 presupuestos"

    def add_arguments(self, parser):
        parser.add_argument(
            "--empresa",
            type=str,
            default="el cacharrito express",
            help="Nombre de la empresa para la cual generar datos",
        )

    def handle(self, *args, **options):
        empresa_nombre = options["empresa"]

        # Buscar empresa
        try:
            empresa = Empresa.objects.get(nombre_taller__icontains=empresa_nombre)
            self.stdout.write(self.style.SUCCESS(f"✓ Empresa encontrada: {empresa.nombre_taller}"))
        except Empresa.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"✗ No se encontró empresa: {empresa_nombre}"))
            self.stdout.write("Empresas disponibles:")
            for emp in Empresa.objects.all()[:10]:
                self.stdout.write(f"  - {emp.nombre_taller}")
            return
        except Empresa.MultipleObjectsReturned:
            empresa = Empresa.objects.filter(nombre_taller__icontains=empresa_nombre).first()
            self.stdout.write(
                self.style.WARNING(
                    f"⚠ Múltiples empresas encontradas, usando: {empresa.nombre_taller}"
                )
            )

        # Crear o obtener técnico
        tecnico, _ = Tecnico.objects.get_or_create(
            empresa=empresa, nombre="Técnico Principal", defaults={"activo": True}
        )

        # Crear o obtener categoría y subcategoría de servicios
        categoria, _ = CategoriaServicio.objects.get_or_create(
            country=empresa.pais,
            code="GEN",
        )
        # Crear nombre para la categoría si no existe
        from taller.servicios.models import CategoriaServicioName

        CategoriaServicioName.objects.get_or_create(
            categoria=categoria, language="es", is_default=True, defaults={"label": "General"}
        )

        subcat, _ = SubcategoriaServicio.objects.get_or_create(
            categoria=categoria,
            country=empresa.pais,
            code="GEN-SUB",
        )

        # Crear repuestos base si no existen
        repuestos = []
        nombres_repuestos = [
            "Filtro de Aceite",
            "Filtro de Aire",
            "Pastillas de Freno",
            "Batería 12V",
            "Aceite Motor 5W-30",
            "Radiador",
            "Termostato",
            "Bomba de Agua",
            "Correa de Distribución",
            "Bujías",
            "Amortiguadores Delanteros",
            "Amortiguadores Traseros",
            "Rótulas",
            "Bieletas",
            "Terminales",
            "Discos de Freno",
            "Tambores de Freno",
        ]

        for nombre in nombres_repuestos[:10]:  # Crear 10 repuestos
            rep, _ = Repuesto.objects.get_or_create(
                empresa=empresa,
                nombre=nombre,
                defaults={
                    "part_number": f"RPT-{nombre[:3].upper()}-{random.randint(100, 999)}",
                    "precio_venta": Decimal(random.randint(5000, 50000)),
                    "precio_compra": Decimal(random.randint(2000, 20000)),
                    "cantidad_stock": random.randint(5, 50),
                },
            )
            repuestos.append(rep)
        self.stdout.write(self.style.SUCCESS(f"✓ {len(repuestos)} repuestos listos"))

        # Crear servicios base si no existen
        servicios = []
        nombres_servicios = [
            "Cambio de Aceite",
            "Alineación y Balanceo",
            "Revisión General",
            "Cambio de Filtros",
            "Revisión de Frenos",
            "Cambio de Batería",
            "Revisión de Suspensión",
            "Limpieza de Inyectores",
            "Diagnóstico Computarizado",
            "Mantenimiento Preventivo",
            "Reparación de Motor",
            "Reparación de Transmisión",
        ]

        for nombre in nombres_servicios[:10]:  # Crear 10 servicios
            serv, _ = Servicio.objects.get_or_create(
                empresa=empresa,
                categoria=categoria,
                subcategoria=subcat,
                nombre=nombre,
                defaults={
                    "precio_base": Decimal(random.randint(10000, 100000)),
                    "activo": True,
                },
            )
            servicios.append(serv)
        self.stdout.write(self.style.SUCCESS(f"✓ {len(servicios)} servicios listos"))

        # Crear otros servicios (servicios externos)
        otros_servicios = []
        nombres_otros = [
            "Pintura Completa",
            "Tapicería",
            "Cristalería",
            "Hojalatería",
            "Enderezado",
            "Soldadura",
        ]

        for nombre in nombres_otros[:6]:
            serv, _ = Servicio.objects.get_or_create(
                empresa=empresa,
                categoria=categoria,
                subcategoria=subcat,
                nombre=nombre,
                defaults={
                    "precio_base": Decimal(random.randint(50000, 200000)),
                    "activo": True,
                },
            )
            otros_servicios.append(serv)
        self.stdout.write(self.style.SUCCESS(f"✓ {len(otros_servicios)} otros servicios listos"))

        # Crear 30 clientes
        clientes = []
        nombres_clientes = [
            "Juan",
            "María",
            "Carlos",
            "Ana",
            "Luis",
            "Laura",
            "Pedro",
            "Carmen",
            "Roberto",
            "Patricia",
            "Fernando",
            "Sandra",
            "Miguel",
            "Andrea",
            "Diego",
            "Natalia",
            "Ricardo",
            "Valentina",
            "Andrés",
            "Camila",
            "Jorge",
            "Isabella",
            "Francisco",
            "Daniela",
            "Sebastián",
            "Francisca",
            "Rodrigo",
            "Javiera",
            "Felipe",
            "Constanza",
        ]

        apellidos = [
            "García",
            "Rodríguez",
            "López",
            "Martínez",
            "González",
            "Pérez",
            "Sánchez",
            "Ramírez",
            "Torres",
            "Flores",
            "Rivera",
            "Gómez",
            "Díaz",
            "Cruz",
            "Morales",
            "Ortiz",
            "Gutiérrez",
            "Chávez",
        ]

        for i, nombre in enumerate(nombres_clientes):
            apellido = random.choice(apellidos)
            email = f"{nombre.lower()}.{apellido.lower()}.{i+1}@test.com"
            cliente, created = Cliente.objects.get_or_create(
                empresa=empresa,
                email=email,
                defaults={
                    "nombre": nombre,
                    "apellido": apellido,
                    "telefono": f"+569{random.randint(10000000, 99999999)}",
                    "direccion": f"Calle {random.randint(1, 9999)}",
                },
            )
            clientes.append(cliente)
        self.stdout.write(self.style.SUCCESS(f"✓ {len(clientes)} clientes creados"))

        # Crear vehículos (algunos clientes con más de un vehículo)
        from taller.models.marca import Marca
        from taller.models.modelo import Modelo

        vehiculos_por_cliente = {}
        nombres_marcas = [
            "Toyota",
            "Nissan",
            "Chevrolet",
            "Ford",
            "Hyundai",
            "Kia",
            "Mazda",
            "Suzuki",
        ]
        nombres_modelos = ["Corolla", "Sentra", "Spark", "Fiesta", "Accent", "Rio", "3", "Swift"]

        # Crear o obtener marcas
        marcas_objs = []
        for nombre_marca in nombres_marcas:
            marca_obj, _ = Marca.objects.get_or_create(
                nombre=nombre_marca,
                country=empresa.pais,
            )
            marcas_objs.append(marca_obj)

        # Crear o obtener modelos
        modelos_objs = []
        for i, nombre_modelo in enumerate(nombres_modelos):
            marca_obj = marcas_objs[i % len(marcas_objs)]
            modelo_obj, _ = Modelo.objects.get_or_create(
                nombre=nombre_modelo,
                marca=marca_obj,
                country=empresa.pais,
            )
            modelos_objs.append(modelo_obj)

        for i, cliente in enumerate(clientes):
            num_vehiculos = random.choices([1, 2, 3], weights=[60, 30, 10])[0]
            vehiculos_cliente = []

            for j in range(num_vehiculos):
                marca_obj = random.choice(marcas_objs)
                modelo_obj = random.choice(modelos_objs)
                año = random.randint(2010, 2024)
                # Generar patente única
                patente = f"{random.choice(['ABCD', 'EFGH', 'IJKL'])}{random.randint(1000, 9999)}"
                # Asegurar unicidad agregando índice si es necesario
                contador = 0
                while Vehiculo.objects.filter(empresa=empresa, patente=patente).exists():
                    patente = (
                        f"{random.choice(['ABCD', 'EFGH', 'IJKL'])}{random.randint(10000, 99999)}"
                    )
                    contador += 1
                    if contador > 100:  # Evitar loop infinito
                        patente = f"TEST-{i}-{j}-{random.randint(100000, 999999)}"
                        break

                vehiculo = Vehiculo.objects.create(
                    empresa=empresa,
                    cliente=cliente,
                    marca=marca_obj,
                    modelo=modelo_obj,
                    anio=año,
                    patente=patente,
                )
                vehiculos_cliente.append(vehiculo)

            vehiculos_por_cliente[cliente.id] = vehiculos_cliente

        total_vehiculos = sum(len(v) for v in vehiculos_por_cliente.values())
        self.stdout.write(self.style.SUCCESS(f"✓ {total_vehiculos} vehículos creados"))

        # Obtener tasa de IVA de la empresa
        from taller.models import ConfiguracionEmpresa

        try:
            config = ConfiguracionEmpresa.objects.get(empresa=empresa)
            tax_rate = config.tasa_impuesto or Decimal("0.19")
        except ConfiguracionEmpresa.DoesNotExist:
            tax_rate = Decimal("0.19")

        # Crear 20 facturas (tipo FAC, estado EMITIDO)
        fecha_base = date.today()
        facturas = []

        for i in range(20):
            cliente = random.choice(clientes)
            vehiculos = vehiculos_por_cliente.get(cliente.id, [])
            vehiculo = random.choice(vehiculos) if vehiculos else None

            fecha = fecha_base - timedelta(days=random.randint(0, 90))
            numero = f"FAC-{fecha.year}-{str(i+1).zfill(4)}"

            doc = Documento.objects.create(
                empresa=empresa,
                tipo="FAC",
                estado="EMITIDO",
                numero=numero,
                fecha_emision=fecha,
                cliente=cliente,
                vehiculo=vehiculo,
                tecnico_responsable=tecnico,
                moneda=empresa.moneda,
                country=empresa.pais,
                tax_rate_applied=tax_rate,
                apply_vat=True,
            )

            # Agregar líneas
            neto_repuestos = Decimal("0")
            neto_servicios = Decimal("0")
            neto_otros = Decimal("0")

            # 1-3 repuestos
            num_repuestos = random.randint(1, 3)
            for _ in range(num_repuestos):
                repuesto = random.choice(repuestos)
                cantidad = random.randint(1, 3)
                precio = repuesto.precio_venta
                descuento = Decimal(random.randint(0, 10)) / 100
                subtotal = precio * Decimal(cantidad) * (1 - descuento)
                neto_repuestos += subtotal

                LineaRepuesto.objects.create(
                    documento=doc,
                    repuesto=repuesto,
                    codigo=repuesto.part_number or f"RPT-{repuesto.id}",
                    nombre=repuesto.nombre,
                    cantidad=cantidad,
                    precio_unitario=precio,
                    descuento=descuento * 100,
                )

            # 1-2 servicios
            num_servicios = random.randint(1, 2)
            for _ in range(num_servicios):
                servicio = random.choice(servicios)
                cantidad = 1
                precio = servicio.precio_base
                descuento = Decimal(random.randint(0, 5)) / 100
                subtotal = precio * Decimal(cantidad) * (1 - descuento)
                neto_servicios += subtotal

                LineaServicio.objects.create(
                    documento=doc,
                    servicio=servicio,
                    nombre=servicio.nombre,
                    cantidad=cantidad,
                    precio_unitario=precio,
                    descuento=descuento * 100,
                )

            # 0-1 otros servicios (50% probabilidad)
            if random.random() < 0.5:
                otro_servicio = random.choice(otros_servicios)
                cantidad = 1
                precio = otro_servicio.precio_base.quantize(Decimal("0.01"))
                costo_interno = (precio * Decimal("0.6")).quantize(
                    Decimal("0.01")
                )  # 60% del precio
                neto_otros += precio

                LineaOtroServicio.objects.create(
                    documento=doc,
                    servicio=otro_servicio,
                    nombre=otro_servicio.nombre,
                    empresa_externa="Taller Externo S.A.",
                    cantidad=cantidad,
                    costo_interno=costo_interno,
                    precio_cliente=precio,
                )

            # Calcular totales
            doc.neto_repuestos = neto_repuestos
            doc.neto_servicios = neto_servicios
            doc.neto_otros_servicios = neto_otros
            doc.tax_amount = neto_repuestos * tax_rate  # IVA solo sobre repuestos
            doc.total = neto_repuestos + neto_servicios + neto_otros + doc.tax_amount
            doc.save()

            facturas.append(doc)

        self.stdout.write(self.style.SUCCESS(f"✓ {len(facturas)} facturas creadas"))

        # Crear 20 órdenes de trabajo (tipo OT, estado EMITIDO o CERRADO)
        ots = []
        for i in range(20):
            cliente = random.choice(clientes)
            vehiculos = vehiculos_por_cliente.get(cliente.id, [])
            vehiculo = random.choice(vehiculos) if vehiculos else None

            fecha = fecha_base - timedelta(days=random.randint(0, 90))
            estado = random.choice(["EMITIDO", "CERRADO"])
            numero = f"OT-{fecha.year}-{str(i+1).zfill(4)}"

            doc = Documento.objects.create(
                empresa=empresa,
                tipo="OT",
                estado=estado,
                numero=numero,
                fecha_emision=fecha,
                cliente=cliente,
                vehiculo=vehiculo,
                tecnico_responsable=tecnico,
                moneda=empresa.moneda,
                country=empresa.pais,
                tax_rate_applied=tax_rate,
                apply_vat=True,
            )

            # Agregar líneas
            neto_repuestos = Decimal("0")
            neto_servicios = Decimal("0")

            # 1-4 repuestos
            num_repuestos = random.randint(1, 4)
            for _ in range(num_repuestos):
                repuesto = random.choice(repuestos)
                cantidad = random.randint(1, 2)
                precio = repuesto.precio_venta
                subtotal = precio * Decimal(cantidad)
                neto_repuestos += subtotal

                LineaRepuesto.objects.create(
                    documento=doc,
                    repuesto=repuesto,
                    codigo=repuesto.part_number or f"RPT-{repuesto.id}",
                    nombre=repuesto.nombre,
                    cantidad=cantidad,
                    precio_unitario=precio,
                    descuento=0,
                )

            # 2-4 servicios
            num_servicios = random.randint(2, 4)
            for _ in range(num_servicios):
                servicio = random.choice(servicios)
                cantidad = 1
                precio = servicio.precio_base
                subtotal = precio * Decimal(cantidad)
                neto_servicios += subtotal

                LineaServicio.objects.create(
                    documento=doc,
                    servicio=servicio,
                    nombre=servicio.nombre,
                    cantidad=cantidad,
                    precio_unitario=precio,
                    descuento=0,
                )

            # Calcular totales
            doc.neto_repuestos = neto_repuestos
            doc.neto_servicios = neto_servicios
            doc.tax_amount = neto_repuestos * tax_rate
            doc.total = neto_repuestos + neto_servicios + doc.tax_amount
            doc.save()

            ots.append(doc)

        self.stdout.write(self.style.SUCCESS(f"✓ {len(ots)} órdenes de trabajo creadas"))

        # Crear 10 presupuestos (tipo PRES, estado BORRADOR o EMITIDO)
        presupuestos = []
        for i in range(10):
            cliente = random.choice(clientes)
            vehiculos = vehiculos_por_cliente.get(cliente.id, [])
            vehiculo = random.choice(vehiculos) if vehiculos else None

            fecha = fecha_base - timedelta(days=random.randint(0, 30))
            estado = random.choice(["BORRADOR", "EMITIDO"])
            numero = f"PRES-{fecha.year}-{str(i+1).zfill(4)}"

            doc = Documento.objects.create(
                empresa=empresa,
                tipo="PRES",
                estado=estado,
                numero=numero,
                fecha_emision=fecha,
                cliente=cliente,
                vehiculo=vehiculo,
                tecnico_responsable=tecnico,
                moneda=empresa.moneda,
                country=empresa.pais,
                tax_rate_applied=tax_rate,
                apply_vat=True,
            )

            # Agregar líneas
            neto_repuestos = Decimal("0")
            neto_servicios = Decimal("0")
            neto_otros = Decimal("0")

            # 1-3 repuestos
            num_repuestos = random.randint(1, 3)
            for _ in range(num_repuestos):
                repuesto = random.choice(repuestos)
                cantidad = random.randint(1, 2)
                precio = repuesto.precio_venta
                subtotal = precio * Decimal(cantidad)
                neto_repuestos += subtotal

                LineaRepuesto.objects.create(
                    documento=doc,
                    repuesto=repuesto,
                    codigo=repuesto.part_number or f"RPT-{repuesto.id}",
                    nombre=repuesto.nombre,
                    cantidad=cantidad,
                    precio_unitario=precio,
                    descuento=0,
                )

            # 1-3 servicios
            num_servicios = random.randint(1, 3)
            for _ in range(num_servicios):
                servicio = random.choice(servicios)
                cantidad = 1
                precio = servicio.precio_base
                subtotal = precio * Decimal(cantidad)
                neto_servicios += subtotal

                LineaServicio.objects.create(
                    documento=doc,
                    servicio=servicio,
                    nombre=servicio.nombre,
                    cantidad=cantidad,
                    precio_unitario=precio,
                    descuento=0,
                )

            # 0-1 otros servicios
            if random.random() < 0.4:
                otro_servicio = random.choice(otros_servicios)
                cantidad = 1
                precio = otro_servicio.precio_base.quantize(Decimal("0.01"))
                costo_interno = (precio * Decimal("0.6")).quantize(Decimal("0.01"))
                neto_otros += precio

                LineaOtroServicio.objects.create(
                    documento=doc,
                    servicio=otro_servicio,
                    nombre=otro_servicio.nombre,
                    empresa_externa="Taller Externo S.A.",
                    cantidad=cantidad,
                    costo_interno=costo_interno,
                    precio_cliente=precio,
                )

            # Calcular totales
            doc.neto_repuestos = neto_repuestos
            doc.neto_servicios = neto_servicios
            doc.neto_otros_servicios = neto_otros
            doc.tax_amount = neto_repuestos * tax_rate
            doc.total = neto_repuestos + neto_servicios + neto_otros + doc.tax_amount
            doc.save()

            presupuestos.append(doc)

        self.stdout.write(self.style.SUCCESS(f"✓ {len(presupuestos)} presupuestos creados"))

        # Resumen final
        self.stdout.write(self.style.SUCCESS("\n" + "=" * 60))
        self.stdout.write(self.style.SUCCESS("RESUMEN DE DATOS GENERADOS"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(f"✓ Clientes: {len(clientes)}")
        self.stdout.write(f"✓ Vehículos: {total_vehiculos}")
        self.stdout.write(f"✓ Facturas: {len(facturas)}")
        self.stdout.write(f"✓ Órdenes de Trabajo: {len(ots)}")
        self.stdout.write(f"✓ Presupuestos: {len(presupuestos)}")
        self.stdout.write(f"✓ Repuestos: {len(repuestos)}")
        self.stdout.write(f"✓ Servicios: {len(servicios)}")
        self.stdout.write(f"✓ Otros Servicios: {len(otros_servicios)}")
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("\n✓ Datos generados exitosamente!"))
        self.stdout.write(self.style.SUCCESS("Ahora puedes revisar el módulo Contador Virtual."))

import datetime
import random
from decimal import Decimal

from faker import Faker

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import connection, transaction

from taller.models.clientes import Cliente
from taller.models.documento import Documento

# Importar modelos
from taller.models.empresa import Empresa
from taller.models.lineas_documento import (
    LineaOtroServicio,
    LineaRepuesto,
    LineaServicio,
)
from taller.models.marca import Marca
from taller.models.modelo import Modelo
from taller.models.repuesto import CategoriaRepuesto, Repuesto
from taller.models.tecnico import Tecnico
from taller.models.vehiculos import Vehiculo
from taller.servicios.models import CategoriaServicio, ServicioExterno


class Command(BaseCommand):
    help = "Seed demo data for USA subscriber (testuser_usa)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete existing demo data before creating new data",
        )
        parser.add_argument(
            "--n", type=int, default=1, help="Scale factor for data volume (default: 1)"
        )

    @transaction.atomic
    def handle(self, *args, **options):
        fake = Faker("en_US")
        User = get_user_model()

        self.stdout.write(self.style.WARNING("🚀 Starting USA demo data seeding..."))

        # 1) Obtener o crear usuario USA
        try:
            user = User.objects.get(username="testuser_usa")
            self.stdout.write(f"✅ Found user: {user.username}")
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR("❌ User 'testuser_usa' not found"))
            return

        # 2) Obtener o crear empresa USA asociada al usuario
        if hasattr(user, "empresa") and user.empresa:
            empresa = user.empresa
            created = False
            self.stdout.write(f"✅ Found existing empresa: {empresa.nombre_taller}")
        else:
            # Crear nueva empresa para el usuario
            empresa = Empresa.objects.create(
                user=user,
                nombre_taller="USA Demo Garage",
                empresa="Demo LLC",
                pais="US",
                direccion=fake.address(),
                telefono=fake.phone_number(),
                email=fake.email(),
                plan="premium",
                moneda="USD",
                zona_horaria="America/New_York",
                suscripcion_activa=True,
            )
            created = True
            self.stdout.write(f"✅ Created empresa: {empresa.nombre_taller}")

        # 3) Configuración de sales tax para USA (7.5%)
        SALES_TAX_RATE = Decimal("0.075")
        self.stdout.write(f"💰 Using sales tax rate: {SALES_TAX_RATE * 100}%")

        # 4) Opcional: flush datos demo existentes
        if options["flush"]:
            self.stdout.write(self.style.WARNING("🗑️ Flushing existing demo data..."))

            # Borrar en orden seguro para evitar problemas de FK
            LineaOtroServicio.objects.filter(documento__empresa=empresa).delete()
            LineaServicio.objects.filter(documento__empresa=empresa).delete()
            LineaRepuesto.objects.filter(documento__empresa=empresa).delete()
            Documento.objects.filter(empresa=empresa).delete()
            Vehiculo.objects.filter(empresa=empresa).delete()
            Cliente.objects.filter(empresa=empresa).delete()
            Repuesto.objects.filter(empresa=empresa).delete()
            ServicioExterno.objects.filter(empresa=empresa).delete()

            self.stdout.write("✅ Demo data flushed")

        # 5) Crear o obtener técnicos
        tecnicos = list(Tecnico.objects.filter(empresa=empresa, activo=True))
        if not tecnicos:
            self.stdout.write("👨‍🔧 Creating technicians...")
            tech_names = ["John Smith", "Mike Johnson", "Sarah Williams"]
            for name in tech_names:
                tecnico = Tecnico.objects.create(
                    empresa=empresa,
                    nombre=name,
                    activo=True,
                    especialidad=random.choice(
                        ["General", "Engine", "Transmission", "Electrical"]
                    ),
                )
                tecnicos.append(tecnico)

        self.stdout.write(f"✅ Available technicians: {len(tecnicos)}")

        # 6) Crear clientes
        n_clientes = 20 * options["n"]
        self.stdout.write(f"👥 Creating {n_clientes} clients...")

        clientes = []
        for i in range(n_clientes):
            nombre_completo = fake.name().split()
            nombre = nombre_completo[0]
            apellido = " ".join(nombre_completo[1:]) if len(nombre_completo) > 1 else ""

            cliente = Cliente.objects.create(
                empresa=empresa,
                nombre=nombre,
                apellido=apellido,
                telefono=fake.phone_number(),
                email=fake.email(),
                direccion=fake.address(),
                tax_id=fake.ein(),
            )
            clientes.append(cliente)

            if (i + 1) % 10 == 0:
                self.stdout.write(f"  📊 Created {i + 1}/{n_clientes} clients")

        # 7) Crear vehículos (40, algunos clientes con >1) - Versión simplificada
        n_vehiculos = 40 * options["n"]
        self.stdout.write(f"🚗 Creating {n_vehiculos} vehicles...")

        # Usar una estrategia más simple: crear vehículos con campos mínimos requeridos
        vehiculos = []

        for i in range(n_vehiculos):
            cliente = random.choice(clientes)
            # Crear VIN único
            vin = fake.unique.bothify(text="1HGCM82633A######")

            try:
                # Intentar obtener marcas y modelos existentes
                marcas_disponibles = list(
                    Marca.objects.all()[:10]
                )  # Limitar a 10 para eficiencia
                if marcas_disponibles:
                    marca = random.choice(marcas_disponibles)
                    # Buscar modelos de esta marca
                    modelos_marca = list(Modelo.objects.filter(marca=marca)[:5])
                    if modelos_marca:
                        modelo = random.choice(modelos_marca)
                    else:
                        # Si no hay modelos, crear uno genérico
                        modelo = Modelo.objects.create(
                            marca=marca,
                            nombre="Demo Model",
                            country=(
                                marca.country if hasattr(marca, "country") else "US"
                            ),
                        )
                else:
                    # Si no hay marcas, crear una básica
                    marca = Marca.objects.create(nombre="Demo Brand", country="US")
                    modelo = Modelo.objects.create(
                        marca=marca, nombre="Demo Model", country="US"
                    )

                vehiculo = Vehiculo.objects.create(
                    empresa=empresa,
                    cliente=cliente,
                    vin=vin,
                    marca=marca,
                    modelo=modelo,
                    anio=random.randint(2010, 2024),
                    patente=fake.unique.license_plate()[:10],  # Limitar longitud
                )
                vehiculos.append(vehiculo)

            except Exception as e:
                self.stdout.write(f"⚠️ Error creating vehicle {i+1}: {e}")
                # Continuar con el siguiente vehículo
                continue

            if (i + 1) % 20 == 0:
                self.stdout.write(
                    f"  📊 Created {len(vehiculos)}/{n_vehiculos} vehicles"
                )

        # 8) Crear repuestos catálogo
        n_repuestos = 50 * options["n"]
        self.stdout.write(f"🔧 Creating {n_repuestos} parts...")

        # Crear categorías de repuestos primero
        categorias_nombres = [
            "Engine",
            "Brake",
            "Electrical",
            "Suspension",
            "Filters",
            "Fluids",
        ]
        categorias = []
        for cat_name in categorias_nombres:
            categoria, created = CategoriaRepuesto.objects.get_or_create(
                empresa=empresa, nombre=cat_name
            )
            categorias.append(categoria)

        repuestos = []
        tipos_repuestos = [
            "Oil Filter",
            "Air Filter",
            "Fuel Filter",
            "Cabin Filter",
            "Brake Pads",
            "Brake Rotors",
            "Brake Fluid",
            "Spark Plugs",
            "Timing Belt",
            "Serpentine Belt",
            "Battery",
            "Alternator",
            "Starter",
            "Radiator",
            "Thermostat",
            "Water Pump",
            "Fuel Pump",
            "Oxygen Sensor",
            "Mass Air Flow Sensor",
            "Transmission Fluid",
            "Power Steering Fluid",
            "Coolant",
            "Shock Absorbers",
            "Struts",
            "Ball Joints",
            "Tie Rods",
        ]

        for i in range(n_repuestos):
            nombre_base = random.choice(tipos_repuestos)
            marca_repuesto = random.choice(
                ["OEM", "Bosch", "Denso", "ACDelco", "Motorcraft", "Gates", "Fram"]
            )

            precio_venta = Decimal(random.randrange(1500, 45000)) / 100  # USD 15–450
            precio_compra = (precio_venta * Decimal(random.uniform(0.5, 0.8))).quantize(
                Decimal("0.01")
            )

            repuesto = Repuesto.objects.create(
                empresa=empresa,
                nombre=f"{marca_repuesto} {nombre_base}",
                part_number=fake.unique.bothify(text="PN-####-???"),
                precio_compra=precio_compra,
                precio_venta=precio_venta,
                cantidad_stock=random.randint(0, 50),  # Usar campo correcto
                categoria=random.choice(categorias),  # Usar instancia, no string
            )
            repuestos.append(repuesto)

            if (i + 1) % 25 == 0:
                self.stdout.write(f"  📊 Created {i + 1}/{n_repuestos} parts")

        # 9) Crear servicios externos
        self.stdout.write("🤝 Creating external services...")
        servicios_externos = []

        # Crear una categoría para servicios externos si no existe
        categoria_externa, created = CategoriaServicio.objects.get_or_create(
            country="US",
            code="external_services",
            defaults={"country": "US", "code": "external_services"},
        )

        empresas_externas = [
            "QuickLube Pro",
            "AutoGlass Experts",
            "Tire World",
            "Paint & Body Shop",
            "Transmission Specialists",
            "AC Repair Center",
            "Towing Services",
        ]

        for empresa_ext in empresas_externas:
            for servicio_tipo in ["Standard Service", "Premium Service"]:
                costo = Decimal(random.randrange(5000, 30000)) / 100
                precio = (costo * Decimal(random.uniform(1.25, 1.5))).quantize(
                    Decimal("0.01")
                )

                servicio_externo = ServicioExterno.objects.create(
                    empresa=empresa,
                    nombre=f"{servicio_tipo} - {empresa_ext}",
                    empresa_externa=empresa_ext,
                    categoria=categoria_externa,
                    descripcion=f"Outsourced {servicio_tipo.lower()} from {empresa_ext}",
                    costo_taller=costo,
                    precio_cliente=precio,
                    activo=True,
                )
                servicios_externos.append(servicio_externo)

        # 10) Crear documentos
        def fecha_aleatoria():
            """Genera fecha aleatoria en los últimos 120 días"""
            days = random.randint(0, 120)
            return datetime.date.today() - datetime.timedelta(days=days)

        # 50 Facturas + 10 Estimados
        n_facturas = 50 * options["n"]
        n_estimados = 10 * options["n"]
        total_docs = n_facturas + n_estimados

        self.stdout.write(
            f"📄 Creating {total_docs} documents ({n_facturas} invoices + {n_estimados} estimates)..."
        )

        tipos_documentos = (["FAC"] * n_facturas) + (["PRES"] * n_estimados)
        random.shuffle(tipos_documentos)

        # Servicios comunes en talleres USA
        servicios_comunes = [
            "Oil Change Service",
            "Brake Pad Replacement",
            "Coolant System Flush",
            "Transmission Service",
            "AC System Check",
            "Battery Replacement",
            "Tire Rotation",
            "Wheel Alignment",
            "Engine Diagnostic",
            "Fuel System Cleaning",
            "Air Filter Replacement",
            "Spark Plug Service",
        ]

        for i, tipo in enumerate(tipos_documentos):
            # Seleccionar cliente y vehículo consistentes
            cliente = random.choice(clientes)
            vehiculos_cliente = [v for v in vehiculos if v.cliente_id == cliente.id]
            vehiculo = (
                random.choice(vehiculos_cliente)
                if vehiculos_cliente
                else random.choice(vehiculos)
            )

            # Crear documento de manera básica evitando campos problemáticos
            try:
                # Generar número secuencial manualmente
                last_doc = (
                    Documento.objects.filter(empresa=empresa, tipo=tipo)
                    .order_by("-numero")
                    .first()
                )
                numero = (last_doc.numero if last_doc and last_doc.numero else 0) + 1

                fecha_emision = fecha_aleatoria()
                total_ejemplo = (
                    Decimal(random.randrange(5000, 50000)) / 100
                )  # USD 50-500

                # Crear documento con campos mínimos
                documento = Documento(
                    empresa=empresa,
                    cliente=cliente,
                    vehiculo=vehiculo,
                    tipo=tipo,
                    numero=numero,
                    estado="EMITIDO",
                    fecha_emision=fecha_emision,
                    moneda="USD",
                    country="US",
                    neto_repuestos=total_ejemplo * Decimal("0.8"),
                    neto_servicios=total_ejemplo * Decimal("0.2"),
                    descuento=Decimal("0.00"),
                    tax_rate_applied=SALES_TAX_RATE * 100,
                    tax_amount=total_ejemplo * SALES_TAX_RATE,
                    total=total_ejemplo,
                )

                # Guardar usando SQL directo para evitar problemas de save()
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO taller_documento 
                        (created_at, updated_at, tipo, numero, estado, fecha_emision, moneda, country,
                         neto_repuestos, neto_servicios, descuento, tax_rate_applied, tax_amount, total,
                         cliente_id, empresa_id, vehiculo_id)
                        VALUES (datetime('now'), datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            tipo,
                            numero,
                            "EMITIDO",
                            fecha_emision.isoformat(),
                            "USD",
                            "US",
                            float(documento.neto_repuestos),
                            float(documento.neto_servicios),
                            float(documento.descuento),
                            float(documento.tax_rate_applied),
                            float(documento.tax_amount),
                            float(documento.total),
                            cliente.pk,
                            empresa.pk,
                            vehiculo.pk if vehiculo else None,
                        ),
                    )

            except Exception as e:
                self.stdout.write(f"⚠️ Error creating document {i+1}: {e}")
                continue

            if (i + 1) % 10 == 0:
                self.stdout.write(
                    f"  📊 Created {i + 1}/{len(tipos_documentos)} documents"
                )

        # Resumen final
        self.stdout.write(self.style.SUCCESS("\n🎉 USA Demo Data Seeding Completed!"))
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(f"📊 Company: {empresa.nombre_taller} ({empresa.pais})")
        self.stdout.write(f"👥 Clients: {len(clientes)}")
        self.stdout.write(f"🚗 Vehicles: {len(vehiculos)}")
        self.stdout.write(f"🔧 Parts: {len(repuestos)}")
        self.stdout.write(f"🤝 External Services: {len(servicios_externos)}")
        self.stdout.write(
            f"📄 Documents: {total_docs} ({n_facturas} invoices + {n_estimados} estimates)"
        )
        self.stdout.write(f"👨‍🔧 Technicians: {len(tecnicos)}")
        self.stdout.write(f"💰 Sales Tax Rate: {SALES_TAX_RATE * 100}%")
        self.stdout.write(self.style.SUCCESS("=" * 50))

        # Instrucciones adicionales
        self.stdout.write(self.style.WARNING("\n📋 Next Steps:"))
        self.stdout.write("• Login as testuser_usa to view the demo data")
        self.stdout.write("• Check Business Intelligence reports")
        self.stdout.write("• Test document creation with the new data")
        self.stdout.write("• Use --flush to regenerate data if needed")
        self.stdout.write("• Use --n=2 for double volume\n")

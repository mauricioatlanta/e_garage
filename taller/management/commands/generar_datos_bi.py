"""
Comando de gestión para generar datos de prueba para el módulo de inteligencia de negocio
"""

import random
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from taller.models.clientes import Cliente
from taller.models.documento import Documento
from taller.models.empresa import Empresa
from taller.models.lineas_documento import LineaRepuesto as RepuestoDocumento
from taller.models.lineas_documento import LineaServicio
from taller.models.repuesto import Repuesto
from taller.models.tecnico import Tecnico
from taller.models.tienda import Tienda


class Command(BaseCommand):
    help = "Genera datos de prueba para el módulo de inteligencia de negocio"

    def add_arguments(self, parser):
        parser.add_argument(
            "--empresa-id", type=int, help="ID de la empresa para la cual generar datos"
        )
        parser.add_argument(
            "--documentos",
            type=int,
            default=50,
            help="Número de documentos a generar (default: 50)",
        )
        parser.add_argument(
            "--dias",
            type=int,
            default=90,
            help="Número de días hacia atrás para generar datos (default: 90)",
        )

    def handle(self, *args, **options):
        empresa_id = options["empresa_id"]
        num_documentos = options["documentos"]
        dias_atras = options["dias"]

        if empresa_id:
            try:
                empresa = Empresa.objects.get(id=empresa_id)
            except Empresa.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"No se encontró la empresa con ID {empresa_id}")
                )
                return
        else:
            # Usar la primera empresa disponible
            empresa = Empresa.objects.first()
            if not empresa:
                self.stdout.write(self.style.ERROR("No hay empresas en el sistema"))
                return

        self.stdout.write(f"🏢 Generando datos para: {empresa.nombre_taller}")

        # Verificar o crear mecánicos
        mecanicos = self.verificar_mecanicos(empresa)

        # Verificar o crear clientes
        clientes = self.verificar_clientes(empresa)

        # Verificar o crear repuestos
        repuestos = self.verificar_repuestos(empresa)

        # Generar documentos
        self.generar_documentos(
            empresa, mecanicos, clientes, repuestos, num_documentos, dias_atras
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Datos de prueba generados exitosamente para {empresa.nombre_taller}"
            )
        )

    def verificar_mecanicos(self, empresa):
        """Verifica que existan mecánicos o los crea"""
        mecanicos = Tecnico.objects.filter(empresa=empresa, activo=True)

        if mecanicos.count() < 3:
            nombres_mecanicos = [
                "Juan Pérez",
                "Carlos Rodríguez",
                "Miguel Ángel Torres",
                "Luis Fernando García",
                "Roberto Silva",
                "Daniel Martínez",
            ]

            for nombre in nombres_mecanicos[:3]:
                mecanico, created = Tecnico.objects.get_or_create(
                    empresa=empresa,
                    nombre=nombre,
                    defaults={
                        "telefono": f"+56 9 {random.randint(10000000, 99999999)}",
                        "activo": True,
                    },
                )
                if created:
                    self.stdout.write(f"  ✓ Mecánico creado: {nombre}")

            mecanicos = Tecnico.objects.filter(empresa=empresa, activo=True)

        self.stdout.write(f"  👨‍🔧 Mecánicos disponibles: {mecanicos.count()}")
        return list(mecanicos)

    def verificar_clientes(self, empresa):
        """Verifica que existan clientes o los crea"""
        clientes = Cliente.objects.filter(empresa=empresa)

        if clientes.count() < 10:
            nombres_clientes = [
                "Ana María González",
                "Pedro Silva",
                "María José Ramírez",
                "Sebastián Torres",
                "Carolina López",
                "Andrés Morales",
                "Valentina Muñoz",
                "Diego Hernández",
                "Francisca Rojas",
                "Maximiliano Castro",
                "Sofía Vargas",
                "Benjamín Soto",
            ]

            for nombre in nombres_clientes[:10]:
                # Separar nombre y apellido
                partes = nombre.split(" ")
                primer_nombre = partes[0]
                apellido = " ".join(partes[1:])

                cliente, created = Cliente.objects.get_or_create(
                    empresa=empresa,
                    nombre=primer_nombre,
                    apellido=apellido,
                    defaults={
                        "telefono": f"+56 9 {random.randint(10000000, 99999999)}",
                        "email": f'{primer_nombre.lower()}.{apellido.lower().replace(" ", "")}@email.com',
                    },
                )
                if created:
                    self.stdout.write(f"  ✓ Cliente creado: {nombre}")

            clientes = Cliente.objects.filter(empresa=empresa)

        self.stdout.write(f"  👥 Clientes disponibles: {clientes.count()}")
        return list(clientes)

    def verificar_repuestos(self, empresa):
        """Verifica que existan repuestos o los crea"""
        tienda, created = Tienda.objects.get_or_create(
            empresa=empresa,
            nombre="Tienda Principal",
            defaults={"direccion": "Dirección de prueba"},
        )

        repuestos = Repuesto.objects.filter(empresa=empresa)

        if repuestos.count() < 20:
            repuestos_data = [
                ("Filtro de Aceite", "FO-001", 15000, 8000),
                ("Pastillas de Freno", "PF-002", 45000, 25000),
                ("Aceite Motor 15W40", "AM-003", 25000, 15000),
                ("Bujías NGK", "BU-004", 8000, 4000),
                ("Filtro de Aire", "FA-005", 18000, 10000),
                ("Amortiguadores", "AM-006", 120000, 80000),
                ("Batería 12V", "BA-007", 80000, 50000),
                ("Neumáticos 185/65R15", "NE-008", 65000, 40000),
                ("Correa de Distribución", "CD-009", 35000, 20000),
                ("Radiador", "RA-010", 150000, 90000),
                ("Alternador", "AL-011", 180000, 120000),
                ("Bomba de Combustible", "BC-012", 95000, 60000),
                ("Sensor de Oxígeno", "SO-013", 75000, 45000),
                ("Discos de Freno", "DF-014", 85000, 55000),
                ("Filtro de Combustible", "FC-015", 22000, 12000),
                ("Termostato", "TE-016", 15000, 8000),
                ("Bomba de Agua", "BA-017", 65000, 40000),
                ("Cable de Bujías", "CB-018", 28000, 16000),
                ("Embrague", "EM-019", 220000, 150000),
                ("Escape Completo", "EC-020", 180000, 120000),
            ]

            for nombre, part_number, precio_venta, precio_compra in repuestos_data:
                repuesto, created = Repuesto.objects.get_or_create(
                    empresa=empresa,
                    tienda=tienda,
                    part_number=part_number,
                    defaults={
                        "nombre_repuesto": nombre,
                        "precio_venta": precio_venta,
                        "precio_compra": precio_compra,
                        "stock": random.randint(10, 100),
                    },
                )
                if created:
                    self.stdout.write(f"  ✓ Repuesto creado: {nombre}")

            repuestos = Repuesto.objects.filter(empresa=empresa)

        self.stdout.write(f"  🔧 Repuestos disponibles: {repuestos.count()}")
        return list(repuestos)

    def generar_documentos(
        self, empresa, mecanicos, clientes, repuestos, num_documentos, dias_atras
    ):
        """Genera documentos de prueba con sus repuestos y servicios"""
        servicios_comunes = [
            ("Cambio de Aceite", 25000),
            ("Alineación y Balanceado", 35000),
            ("Revisión de Frenos", 20000),
            ("Diagnóstico Computarizado", 30000),
            ("Cambio de Pastillas", 40000),
            ("Mantenimiento Preventivo", 50000),
            ("Reparación Motor", 150000),
            ("Cambio de Embrague", 180000),
            ("Reparación Sistema Eléctrico", 80000),
            ("Cambio de Amortiguadores", 120000),
            ("Reparación de Escape", 60000),
            ("Sincronización", 45000),
        ]

        fecha_inicio = timezone.now().date() - timedelta(days=dias_atras)

        for i in range(num_documentos):
            # Generar fecha aleatoria
            dias_random = random.randint(0, dias_atras)
            fecha_documento = fecha_inicio + timedelta(days=dias_random)

            # Crear documento
            documento = Documento.objects.create(
                empresa=empresa,
                tipo_documento=random.choice(
                    ["Presupuesto", "Orden de trabajo", "Factura"]
                ),
                numero_documento=f"DOC-{random.randint(1000, 9999)}-{i}",
                fecha=fecha_documento,
                cliente=random.choice(clientes),
                mecanico=random.choice(mecanicos),
                kilometraje=random.randint(50000, 200000),
                observaciones=f"Documento de prueba {i+1}",
            )

            # Agregar repuestos (0-5 repuestos por documento)
            num_repuestos = random.randint(0, 5)
            repuestos_documento = random.sample(
                repuestos, min(num_repuestos, len(repuestos))
            )

            for repuesto in repuestos_documento:
                cantidad = random.randint(1, 4)
                # Precio con variación del ±10%
                precio_base = repuesto.precio_venta
                variacion = random.uniform(0.9, 1.1)
                precio_final = int(precio_base * variacion)

                RepuestoDocumento.objects.create(
                    documento=documento,
                    repuesto=repuesto,
                    codigo=repuesto.part_number,
                    nombre=repuesto.nombre_repuesto,
                    cantidad=cantidad,
                    precio_unitario=precio_final,
                )

            # Agregar servicios (1-3 servicios por documento)
            num_servicios = random.randint(1, 3)
            servicios_documento = random.sample(
                servicios_comunes, min(num_servicios, len(servicios_comunes))
            )

            for nombre_servicio, precio_base in servicios_documento:
                # Precio con variación del ±15%
                variacion = random.uniform(0.85, 1.15)
                precio_final = int(precio_base * variacion)

                LineaServicio.objects.create(
                    empresa=empresa,
                    documento=documento,
                    nombre=nombre_servicio,
                    precio_unitario=precio_final,
                )

            if (i + 1) % 10 == 0:
                self.stdout.write(
                    f"  📄 Generados {i + 1}/{num_documentos} documentos..."
                )

        self.stdout.write(f"  📊 Total documentos generados: {num_documentos}")

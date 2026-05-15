from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from taller.models.documento import Documento
from taller.models.lineas_documento import LineaRepuesto, LineaServicio


class Command(BaseCommand):
    help = "Diagnosticar y reparar problemas con totales de documentos"

    def add_arguments(self, parser):
        parser.add_argument(
            "--fix",
            action="store_true",
            help="Crear datos de prueba para solucionar problemas de totales",
        )

    def handle(self, *args, **options):
        self.stdout.write("🔍 DIAGNÓSTICO DE TOTALES DE DOCUMENTOS")
        self.stdout.write("=" * 50)

        # 1. Verificar usuarios
        users = User.objects.all()
        self.stdout.write(f"👥 Total usuarios: {users.count()}")

        # 2. Verificar documentos
        documentos = Documento.objects.all()
        self.stdout.write(f"📄 Total documentos: {documentos.count()}")

        # 3. Verificar líneas
        lineas_repuesto = LineaRepuesto.objects.all()
        lineas_servicio = LineaServicio.objects.all()
        self.stdout.write(f"🔧 Total líneas repuesto: {lineas_repuesto.count()}")
        self.stdout.write(f"⚙️ Total líneas servicio: {lineas_servicio.count()}")

        # 4. Analizar documentos uno por uno
        self.stdout.write("\n📋 ANÁLISIS DE DOCUMENTOS:")
        for doc in documentos[:5]:
            self.stdout.write(f"\n--- Documento {doc.numero} ---")
            try:
                self.stdout.write(
                    f"Empresa: {doc.empresa.nombre if doc.empresa else 'Sin empresa'}"
                )
            except:
                self.stdout.write("Empresa: Error al acceder")

            lineas_rep = doc.lineas_repuesto.count()
            lineas_ser = doc.lineas_servicio.count()

            self.stdout.write(f"Líneas repuesto: {lineas_rep}")
            self.stdout.write(f"Líneas servicio: {lineas_ser}")

            try:
                total_rep = doc.total_repuestos()
                total_ser = doc.total_servicios()
                total_gen = doc.total_general()

                self.stdout.write(f"Total repuestos: ${total_rep}")
                self.stdout.write(f"Total servicios: ${total_ser}")
                self.stdout.write(f"Total general: ${total_gen}")
            except Exception as e:
                self.stdout.write(f"❌ Error calculando totales: {e}")

        # 5. Si se especifica --fix, crear datos de prueba
        if options["fix"]:
            self.stdout.write("\n🔧 CREANDO DATOS DE PRUEBA...")
            self.crear_datos_prueba()

    def crear_datos_prueba(self):
        try:
            # Buscar primer usuario
            user = User.objects.first()
            if not user:
                self.stdout.write("❌ No hay usuarios en el sistema")
                return

            # Buscar o crear documento
            documento, created = Documento.objects.get_or_create(
                numero=9999,
                defaults={
                    "tipo": "COTIZACION",
                    "fecha": "2025-08-21",
                    "descuento": Decimal("0.00"),
                    "tax_rate_applied": Decimal("19.00"),
                },
            )

            if created:
                self.stdout.write(f"✅ Documento {documento.numero} creado")
            else:
                self.stdout.write(f"📋 Documento {documento.numero} ya existe")

            # Agregar líneas de repuestos si no existen
            if not documento.lineas_repuesto.exists():
                LineaRepuesto.objects.create(
                    documento=documento,
                    codigo="REP001",
                    nombre="Filtro de Aceite",
                    cantidad=2,
                    precio_unitario=Decimal("15000.00"),
                    descuento=Decimal("0.00"),
                )

                LineaRepuesto.objects.create(
                    documento=documento,
                    codigo="REP002",
                    nombre="Pastillas de Freno",
                    cantidad=1,
                    precio_unitario=Decimal("45000.00"),
                    descuento=Decimal("10.00"),
                )

                self.stdout.write("✅ Líneas de repuesto creadas")

            # Agregar líneas de servicios si no existen
            if not documento.lineas_servicio.exists():
                LineaServicio.objects.create(
                    documento=documento,
                    codigo="SER001",
                    nombre="Cambio de Aceite",
                    cantidad=1,
                    precio_unitario=Decimal("25000.00"),
                    descuento=Decimal("0.00"),
                )

                LineaServicio.objects.create(
                    documento=documento,
                    codigo="SER002",
                    nombre="Revisión General",
                    cantidad=1,
                    precio_unitario=Decimal("35000.00"),
                    descuento=Decimal("5.00"),
                )

                self.stdout.write("✅ Líneas de servicio creadas")

            # Verificar totales finales
            self.stdout.write(f"\n📊 TOTALES FINALES DEL DOCUMENTO {documento.numero}:")
            self.stdout.write(f"   Total Repuestos: ${documento.total_repuestos()}")
            self.stdout.write(f"   Total Servicios: ${documento.total_servicios()}")
            self.stdout.write(f"   Total General: ${documento.total_general()}")

        except Exception as e:
            self.stdout.write(f"❌ Error creando datos: {e}")
            import traceback

            self.stdout.write(traceback.format_exc())

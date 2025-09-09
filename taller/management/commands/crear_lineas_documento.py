from decimal import Decimal

from django.core.management.base import BaseCommand

from taller.models.documento import Documento
from taller.models.lineas_documento import LineaRepuesto, LineaServicio


class Command(BaseCommand):
    help = 'Crear líneas de documento para solucionar totales en $0'
    
    def handle(self, *args, **options):
        # Verificar documentos existentes
        documentos = Documento.objects.all()
        self.stdout.write(f"📄 Total documentos: {documentos.count()}")
        
        if not documentos.exists():
            self.stdout.write(self.style.ERROR("❌ No hay documentos en la base de datos"))
            return
        
        # Verificar líneas existentes
        total_lineas_rep = LineaRepuesto.objects.count()
        total_lineas_serv = LineaServicio.objects.count()
        self.stdout.write(f"📊 Líneas existentes - Repuestos: {total_lineas_rep}, Servicios: {total_lineas_serv}")
        
        # Tomar el primer documento para agregar líneas
        documento = documentos.first()
        self.stdout.write(f"🎯 Trabajando con documento: {documento.numero} ({documento.tipo})")
        
        # Verificar estado actual del documento
        lineas_rep_actual = documento.lineas_repuesto.count()
        lineas_serv_actual = documento.lineas_servicio.count()
        self.stdout.write(f"📋 Estado actual - Repuestos: {lineas_rep_actual}, Servicios: {lineas_serv_actual}")
        
        # Agregar líneas de repuesto si no existen
        if lineas_rep_actual == 0:
            self.stdout.write("🔧 Agregando líneas de repuesto...")
            
            linea1 = LineaRepuesto.objects.create(
                documento=documento,
                codigo="REP001",
                nombre="Filtro de Aceite",
                cantidad=2,
                precio_unitario=Decimal('15000.00'),
                descuento=Decimal('0.00')
            )
            
            linea2 = LineaRepuesto.objects.create(
                documento=documento,
                codigo="REP002", 
                nombre="Pastillas de Freno",
                cantidad=1,
                precio_unitario=Decimal('45000.00'),
                descuento=Decimal('10.00')
            )
            
            self.stdout.write(self.style.SUCCESS(f"✅ Líneas de repuesto creadas:"))
            self.stdout.write(f"   - {linea1.nombre}: {linea1.cantidad} x ${linea1.precio_unitario} = ${linea1.subtotal}")
            self.stdout.write(f"   - {linea2.nombre}: {linea2.cantidad} x ${linea2.precio_unitario} (desc. {linea2.descuento}%) = ${linea2.subtotal}")
        
        # Agregar líneas de servicio si no existen
        if lineas_serv_actual == 0:
            self.stdout.write("⚙️ Agregando líneas de servicio...")
            
            linea3 = LineaServicio.objects.create(
                documento=documento,
                codigo="SER001",
                nombre="Cambio de Aceite",
                cantidad=1,
                precio_unitario=Decimal('25000.00'),
                descuento=Decimal('0.00')
            )
            
            linea4 = LineaServicio.objects.create(
                documento=documento,
                codigo="SER002",
                nombre="Revisión General",
                cantidad=1,
                precio_unitario=Decimal('35000.00'),
                descuento=Decimal('5.00')
            )
            
            self.stdout.write(self.style.SUCCESS(f"✅ Líneas de servicio creadas:"))
            self.stdout.write(f"   - {linea3.nombre}: {linea3.cantidad} x ${linea3.precio_unitario} = ${linea3.subtotal}")
            self.stdout.write(f"   - {linea4.nombre}: {linea4.cantidad} x ${linea4.precio_unitario} (desc. {linea4.descuento}%) = ${linea4.subtotal}")
        
        # Verificar totales finales
        self.stdout.write(f"\n📊 TOTALES CALCULADOS:")
        try:
            total_rep = documento.total_repuestos()
            total_serv = documento.total_servicios()
            total_gen = documento.total_general()
            
            self.stdout.write(f"   Total Repuestos: ${total_rep}")
            self.stdout.write(f"   Total Servicios: ${total_serv}")
            self.stdout.write(f"   Total General: ${total_gen}")
            
            if total_rep > 0 or total_serv > 0:
                self.stdout.write(self.style.SUCCESS(f"\n🎉 ¡ÉXITO! Los totales ahora aparecerán en la vista de lista"))
                self.stdout.write(f"Recargar: http://127.0.0.1:8000/us/documentos/us/ o http://127.0.0.1:8000/cl/documentos/cl/")
            else:
                self.stdout.write(self.style.WARNING(f"\n⚠️ Los totales siguen en 0 - revisar cálculos"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error calculando totales: {e}"))

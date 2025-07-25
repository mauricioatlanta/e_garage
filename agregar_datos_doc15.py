import os
import django
import sys
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings_sqlite')
django.setup()

from taller.models.documento import Documento, RepuestoDocumento, ServicioDocumento
from taller.models.mecanico import Mecanico

def agregar_datos_documento_15():
    """Agregar datos al documento #15 para testing de edición"""
    
    print("🔧 AGREGANDO DATOS AL DOCUMENTO #15")
    
    try:
        documento = Documento.objects.get(id=15)
        print(f"📋 Documento encontrado: {documento.tipo_documento} #{documento.numero_documento}")
        
        # Agregar mecánico
        mecanico, _ = Mecanico.objects.get_or_create(nombre="Juan Pérez")
        documento.mecanico = mecanico
        documento.save()
        print(f"🔧 Mecánico asignado: {mecanico.nombre}")
        
        # Agregar repuestos
        repuestos_data = [
            {"codigo": "FIL001", "nombre": "Filtro de aceite Toyota", "cantidad": 2, "precio": 15000},
            {"codigo": "ACE001", "nombre": "Aceite 5W30 4L", "cantidad": 1, "precio": 35000},
        ]
        
        for rep_data in repuestos_data:
            repuesto = RepuestoDocumento.objects.create(
                documento=documento,
                codigo=rep_data["codigo"],
                nombre=rep_data["nombre"],
                cantidad=rep_data["cantidad"],
                precio=rep_data["precio"]
            )
            print(f"🔩 Repuesto agregado: {repuesto.nombre}")
        
        # Agregar servicios
        servicios_data = [
            {"nombre": "Cambio de aceite completo", "precio": 25000},
            {"nombre": "Revisión de frenos", "precio": 15000},
        ]
        
        empresa = documento.empresa
        for serv_data in servicios_data:
            servicio = ServicioDocumento.objects.create(
                empresa=empresa,
                documento=documento,
                nombre=serv_data["nombre"],
                precio=serv_data["precio"]
            )
            print(f"⚙️ Servicio agregado: {servicio.nombre}")
        
        # Verificar totales
        repuestos = RepuestoDocumento.objects.filter(documento=documento)
        servicios = ServicioDocumento.objects.filter(documento=documento)
        
        total_repuestos = sum(r.total for r in repuestos)
        total_servicios = sum(s.precio for s in servicios)
        total_general = total_repuestos + total_servicios
        
        print(f"\n💰 TOTALES CALCULADOS:")
        print(f"   Repuestos: ${total_repuestos}")
        print(f"   Servicios: ${total_servicios}")
        print(f"   TOTAL: ${total_general}")
        
        print(f"\n🔗 URL para probar edición: http://127.0.0.1:8000/documentos/editar/15/")
        
        return True
        
    except Documento.DoesNotExist:
        print("❌ Documento #15 no encontrado")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    agregar_datos_documento_15()

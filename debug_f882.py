import os
import django
import sys
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings_sqlite')
django.setup()

from taller.models.documento import Documento, RepuestoDocumento, ServicioDocumento

def debug_documento_f882():
    """Debug específico para el documento F-882"""
    
    print("🔍 DEBUG: Documento F-882")
    print("=" * 50)
    
    try:
        # Buscar el documento F-882
        documento = Documento.objects.get(numero_documento="F-882")
        
        print(f"📋 DOCUMENTO ENCONTRADO:")
        print(f"   ID: {documento.id}")
        print(f"   Tipo: {documento.tipo_documento}")
        print(f"   Número: {documento.numero_documento}")
        print(f"   Fecha: {documento.fecha}")
        print(f"   Cliente: {documento.cliente.nombre if documento.cliente else 'Sin cliente'}")
        print(f"   Vehículo: {documento.vehiculo.patente if documento.vehiculo else 'Sin vehículo'}")
        print(f"   Empresa: {documento.empresa.nombre_taller if documento.empresa else 'Sin empresa'}")
        print(f"   Kilometraje: {documento.kilometraje}")
        
        # Verificar repuestos asociados
        repuestos = RepuestoDocumento.objects.filter(documento=documento)
        print(f"\n🔩 REPUESTOS ({repuestos.count()}):")
        if repuestos.exists():
            for rep in repuestos:
                print(f"   - ID: {rep.id}")
                print(f"     Código: {rep.codigo}")
                print(f"     Nombre: {rep.nombre}")
                print(f"     Cantidad: {rep.cantidad}")
                print(f"     Precio: ${rep.precio}")
                print(f"     Total: ${rep.total}")
        else:
            print("   ❌ No hay repuestos asociados")
        
        # Verificar servicios asociados
        servicios = ServicioDocumento.objects.filter(documento=documento)
        print(f"\n⚙️ SERVICIOS ({servicios.count()}):")
        if servicios.exists():
            for serv in servicios:
                print(f"   - ID: {serv.id}")
                print(f"     Nombre: {serv.nombre}")
                print(f"     Precio: ${serv.precio}")
                print(f"     Empresa: {serv.empresa.nombre_taller if serv.empresa else 'Sin empresa'}")
        else:
            print("   ❌ No hay servicios asociados")
        
        # Calcular totales
        total_repuestos = sum(r.total for r in repuestos)
        total_servicios = sum(s.precio for s in servicios)
        total_general = total_repuestos + total_servicios
        
        print(f"\n💰 TOTALES:")
        print(f"   Repuestos: ${total_repuestos}")
        print(f"   Servicios: ${total_servicios}")
        print(f"   TOTAL: ${total_general}")
        
        # URLs para testing
        print(f"\n🔗 URLS:")
        print(f"   Ver: http://127.0.0.1:8000/documentos/{documento.id}/")
        print(f"   Editar: http://127.0.0.1:8000/documentos/editar/{documento.id}/")
        
        return documento
        
    except Documento.DoesNotExist:
        print("❌ Documento F-882 no encontrado")
        
        # Buscar documentos similares
        documentos_factura = Documento.objects.filter(tipo_documento="Factura").order_by('-id')[:5]
        print(f"\n📋 ÚLTIMAS 5 FACTURAS:")
        for doc in documentos_factura:
            repuestos_count = RepuestoDocumento.objects.filter(documento=doc).count()
            servicios_count = ServicioDocumento.objects.filter(documento=doc).count()
            print(f"   - {doc.numero_documento}: {repuestos_count} repuestos, {servicios_count} servicios")
        
        return None

def verificar_vista_detalle():
    """Verificar que la vista de detalle esté funcionando correctamente"""
    
    print("\n🔍 VERIFICANDO VISTA DE DETALLE")
    print("=" * 50)
    
    # Obtener documentos recientes con repuestos
    documentos_con_repuestos = []
    documentos = Documento.objects.all().order_by('-id')[:10]
    
    for doc in documentos:
        repuestos = RepuestoDocumento.objects.filter(documento=doc)
        if repuestos.exists():
            documentos_con_repuestos.append((doc, repuestos.count()))
    
    print(f"📊 DOCUMENTOS CON REPUESTOS:")
    for doc, count in documentos_con_repuestos:
        print(f"   - {doc.numero_documento}: {count} repuestos")
        print(f"     URL: http://127.0.0.1:8000/documentos/{doc.id}/")
    
    if not documentos_con_repuestos:
        print("   ❌ No hay documentos con repuestos para testing")

def agregar_repuesto_test_f882():
    """Agregar un repuesto de prueba al documento F-882"""
    
    print("\n🧪 AGREGANDO REPUESTO TEST A F-882")
    
    try:
        documento = Documento.objects.get(numero_documento="F-882")
        
        # Eliminar repuestos existentes para evitar duplicados
        RepuestoDocumento.objects.filter(documento=documento).delete()
        
        # Crear repuesto de prueba
        repuesto = RepuestoDocumento.objects.create(
            documento=documento,
            codigo="FIL001",
            nombre="Filtro de aceite Toyota",
            cantidad=1,
            precio=15000
        )
        
        print(f"✅ Repuesto agregado:")
        print(f"   ID: {repuesto.id}")
        print(f"   Código: {repuesto.codigo}")
        print(f"   Nombre: {repuesto.nombre}")
        print(f"   Precio: ${repuesto.precio}")
        print(f"   Total: ${repuesto.total}")
        
        print(f"\n🔗 Ver documento actualizado: http://127.0.0.1:8000/documentos/{documento.id}/")
        
        return repuesto
        
    except Documento.DoesNotExist:
        print("❌ Documento F-882 no encontrado para agregar repuesto")
        return None

if __name__ == "__main__":
    documento = debug_documento_f882()
    verificar_vista_detalle()
    
    if documento:
        agregar_repuesto_test_f882()
        print("\n" + "="*50)
        debug_documento_f882()  # Verificar nuevamente después de agregar

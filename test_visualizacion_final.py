import os
import django
import sys
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings_sqlite')
django.setup()

from taller.models.documento import Documento, RepuestoDocumento, ServicioDocumento

def test_final_visualizacion():
    """Test final para verificar que los datos se muestran correctamente"""
    
    print("🔍 TEST FINAL: Visualización de Documentos")
    print("=" * 60)
    
    # Verificar documento F-882
    try:
        documento = Documento.objects.get(numero_documento="F-882")
        
        print(f"📋 DOCUMENTO F-882 (ID: {documento.id})")
        print(f"   Cliente: {documento.cliente.nombre}")
        print(f"   Vehículo: {documento.vehiculo.patente}")
        print(f"   Empresa: {documento.empresa.nombre_taller}")
        
        # Verificar repuestos usando consulta directa
        repuestos = RepuestoDocumento.objects.filter(documento=documento)
        print(f"\n🔩 REPUESTOS ({repuestos.count()}):")
        for rep in repuestos:
            print(f"   - {rep.codigo}: {rep.nombre}")
            print(f"     Cantidad: {rep.cantidad}, Precio: ${rep.precio}")
            print(f"     Total: ${rep.total}")
        
        # Verificar servicios usando consulta directa
        servicios = ServicioDocumento.objects.filter(documento=documento)
        print(f"\n⚙️ SERVICIOS ({servicios.count()}):")
        for serv in servicios:
            print(f"   - {serv.nombre}: ${serv.precio}")
        
        # Calcular totales
        total_repuestos = sum(r.total for r in repuestos)
        total_servicios = sum(s.precio for s in servicios)
        subtotal = total_repuestos + total_servicios
        iva = subtotal * 0.19
        total_con_iva = subtotal + iva
        
        print(f"\n💰 CÁLCULOS:")
        print(f"   Subtotal repuestos: ${total_repuestos}")
        print(f"   Subtotal servicios: ${total_servicios}")
        print(f"   Subtotal total: ${subtotal}")
        print(f"   IVA (19%): ${iva:.0f}")
        print(f"   TOTAL CON IVA: ${total_con_iva:.0f}")
        
        # Verificar si el problema es con related_name
        print(f"\n🔗 TESTING RELATED_NAME:")
        try:
            repuestos_related = documento.repuestos.all()
            print(f"   ✅ documento.repuestos.all() funciona: {repuestos_related.count()} items")
        except Exception as e:
            print(f"   ❌ documento.repuestos.all() falla: {e}")
        
        try:
            servicios_related = documento.servicios.all()
            print(f"   ✅ documento.servicios.all() funciona: {servicios_related.count()} items")
        except Exception as e:
            print(f"   ❌ documento.servicios.all() falla: {e}")
        
        # URLs de testing
        print(f"\n🌐 URLs PARA VERIFICACIÓN MANUAL:")
        print(f"   📄 Ver documento: http://127.0.0.1:8000/documentos/{documento.id}/")
        print(f"   ✏️ Editar documento: http://127.0.0.1:8000/documentos/editar/{documento.id}/")
        
        # Estado esperado vs real
        print(f"\n📊 RESUMEN:")
        if repuestos.exists():
            print(f"   ✅ Documento TIENE repuestos en BD")
        else:
            print(f"   ❌ Documento NO TIENE repuestos en BD")
        
        if servicios.exists():
            print(f"   ✅ Documento TIENE servicios en BD")
        else:
            print(f"   ❌ Documento NO TIENE servicios en BD")
        
        return True
        
    except Documento.DoesNotExist:
        print("❌ Documento F-882 no existe")
        return False

def verificar_otros_documentos():
    """Verificar otros documentos para comparación"""
    
    print(f"\n🔍 VERIFICANDO OTROS DOCUMENTOS CON DATOS:")
    
    # Buscar documentos con repuestos
    documentos_con_repuestos = []
    for doc in Documento.objects.all():
        repuestos_count = RepuestoDocumento.objects.filter(documento=doc).count()
        if repuestos_count > 0:
            documentos_con_repuestos.append((doc, repuestos_count))
    
    print(f"📊 DOCUMENTOS CON REPUESTOS ({len(documentos_con_repuestos)}):")
    for doc, count in documentos_con_repuestos:
        print(f"   - {doc.numero_documento}: {count} repuestos")
        print(f"     URL: http://127.0.0.1:8000/documentos/{doc.id}/")

if __name__ == "__main__":
    test_final_visualizacion()
    verificar_otros_documentos()

import os
import django
import sys
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings_sqlite')
django.setup()

from django.contrib.auth.models import User
from taller.models.empresa import Empresa
from taller.models.documento import Documento, RepuestoDocumento, ServicioDocumento

def debug_problema_multiempresa():
    """Debug del problema de pérdida de datos en taller2"""
    
    print("🔍 DEBUG: Problema Pérdida de Datos por Empresa")
    print("=" * 60)
    
    # 1. Analizar todas las empresas y sus documentos
    empresas = Empresa.objects.all()
    print(f"🏢 Total empresas: {empresas.count()}")
    
    for empresa in empresas:
        documentos = Documento.objects.filter(empresa=empresa)
        print(f"\n🏢 EMPRESA: {empresa.nombre_taller}")
        print(f"   👤 Usuario: {empresa.usuario.username if empresa.usuario else 'Sin usuario'}")
        print(f"   📄 Documentos: {documentos.count()}")
        
        # Analizar documentos recientes de esta empresa
        docs_recientes = documentos.order_by('-id')[:3]
        for doc in docs_recientes:
            repuestos = RepuestoDocumento.objects.filter(documento=doc)
            servicios = ServicioDocumento.objects.filter(documento=doc)
            
            print(f"   📋 Doc #{doc.id} ({doc.tipo_documento} {doc.numero_documento}):")
            print(f"      - Cliente: {doc.cliente.nombre if doc.cliente else 'Sin cliente'}")
            print(f"      - Mecánico: {doc.mecanico.nombre if doc.mecanico else 'Sin mecánico'}")
            print(f"      - Repuestos: {repuestos.count()}")
            for rep in repuestos:
                print(f"        * {rep.nombre}: ${rep.precio} x {rep.cantidad}")
            print(f"      - Servicios: {servicios.count()}")
            for serv in servicios:
                print(f"        * {serv.nombre}: ${serv.precio}")
            
            total_rep = sum(r.total for r in repuestos)
            total_serv = sum(s.precio for s in servicios)
            print(f"      - Total: ${total_rep + total_serv}")
            
            # Estado del documento
            if repuestos.exists() or servicios.exists():
                print(f"      - Estado: ✅ Tiene datos")
            else:
                print(f"      - Estado: ❌ Sin repuestos/servicios")
    
    # 2. Buscar documentos problemáticos (sin datos)
    print(f"\n🔍 DOCUMENTOS PROBLEMÁTICOS (sin repuestos ni servicios):")
    docs_vacios = []
    for doc in Documento.objects.all():
        repuestos = RepuestoDocumento.objects.filter(documento=doc)
        servicios = ServicioDocumento.objects.filter(documento=doc)
        if not repuestos.exists() and not servicios.exists():
            docs_vacios.append(doc)
    
    if docs_vacios:
        for doc in docs_vacios:
            print(f"   ❌ Doc #{doc.id} ({doc.empresa.nombre_taller}): {doc.tipo_documento} {doc.numero_documento}")
    else:
        print(f"   ✅ No hay documentos vacíos")
    
    # 3. URLs de testing por empresa
    print(f"\n🌐 URLS PARA TESTING POR EMPRESA:")
    for empresa in empresas:
        usuario = empresa.usuario
        if usuario:
            print(f"   🏢 {empresa.nombre_taller} (Usuario: {usuario.username}):")
            print(f"      📄 Crear: http://127.0.0.1:8000/documentos/nuevo/")
            print(f"      📋 Lista: http://127.0.0.1:8000/documentos/")

def crear_documento_test_empresa():
    """Crear un documento de prueba para testing en taller2"""
    print(f"\n🧪 CREANDO DOCUMENTO TEST PARA TODAS LAS EMPRESAS")
    
    # Obtener todas las empresas
    empresas = Empresa.objects.all()
    
    for empresa in empresas:
        if not empresa.usuario:
            print(f"   ⚠️ {empresa.nombre_taller}: Sin usuario asignado")
            continue
            
        from taller.models.clientes import Cliente
        from taller.models.mecanico import Mecanico
        from datetime import date
        
        # Obtener o crear cliente para esta empresa
        cliente = Cliente.objects.filter(empresa=empresa).first()
        if not cliente:
            cliente = Cliente.objects.create(
                empresa=empresa,
                nombre=f"Cliente Test {empresa.nombre_taller}",
                apellido="Testing",
                telefono="123456789"
            )
        
        # Obtener o crear mecánico
        mecanico, _ = Mecanico.objects.get_or_create(
            nombre=f"Mecánico Test {empresa.nombre_taller[:10]}"
        )
        
        # Crear documento
        count = Documento.objects.filter(empresa=empresa).count()
        documento = Documento.objects.create(
            empresa=empresa,
            tipo_documento="Presupuesto",
            numero_documento=f"TEST-{empresa.id}-{count+1:03d}",
            fecha=date.today(),
            cliente=cliente,
            mecanico=mecanico,
            kilometraje=100000
        )
        
        # Agregar repuesto
        repuesto = RepuestoDocumento.objects.create(
            documento=documento,
            codigo="TEST001",
            nombre=f"Repuesto Test {empresa.nombre_taller}",
            cantidad=1,
            precio=25000
        )
        
        # Agregar servicio
        servicio = ServicioDocumento.objects.create(
            empresa=empresa,
            documento=documento,
            nombre=f"Servicio Test {empresa.nombre_taller}",
            precio=35000
        )
        
        print(f"   ✅ {empresa.nombre_taller}: Doc #{documento.id} creado")
        print(f"      🔗 Ver: http://127.0.0.1:8000/documentos/{documento.id}/")

if __name__ == "__main__":
    debug_problema_multiempresa()
    crear_documento_test_empresa()
    print("\n" + "="*60)
    debug_problema_multiempresa()  # Re-ejecutar para ver cambios

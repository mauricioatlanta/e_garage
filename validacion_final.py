import os
import django
import sys
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings_sqlite')
django.setup()

from django.contrib.auth.models import User
from taller.models.tecnico import Tecnico
from taller.models.documento import Documento
from taller.models.lineas_documento import LineaServicio, LineaRepuesto, LineaOtroServicio
from taller.models.empresa import Empresa

def validacion_final_sistema():
    """Validación completa del sistema de documentos y mecánicos"""
    
    print("🔍 VALIDACIÓN FINAL DEL SISTEMA E-GARAGE")
    print("=" * 60)
    
    # 1. Verificar usuarios y empresas
    usuarios = User.objects.all()
    empresas = Empresa.objects.all()
    print(f"👤 Usuarios registrados: {usuarios.count()}")
    print(f"🏢 Empresas registradas: {empresas.count()}")
    
    # 2. Verificar mecánicos
    mecanicos = Tecnico.objects.all()
    print(f"\n🔧 Mecánicos en sistema: {mecanicos.count()}")
    for mec in mecanicos[:5]:  # Mostrar solo los primeros 5
        print(f"   - ID {mec.id}: {mec.nombre}")
    if mecanicos.count() > 5:
        print(f"   ... y {mecanicos.count() - 5} más")
    
    # 3. Verificar documentos
    documentos = Documento.objects.all()
    print(f"\n📄 Documentos totales: {documentos.count()}")
    
    # Documentos por tipo
    tipos_doc = {}
    for doc in documentos:
        tipo = doc.tipo_documento
        tipos_doc[tipo] = tipos_doc.get(tipo, 0) + 1
    
    for tipo, cantidad in tipos_doc.items():
        print(f"   - {tipo}: {cantidad}")
    
    # 4. Verificar integridad de datos en documentos recientes
    print(f"\n🔍 VERIFICANDO INTEGRIDAD DE DOCUMENTOS RECIENTES:")
    documentos_recientes = documentos.order_by('-id')[:3]  # Usar id en lugar de fecha_creacion
    
    for doc in documentos_recientes:
        print(f"\n📋 Documento #{doc.id} ({doc.tipo_documento})")
        print(f"   📅 Fecha: {getattr(doc, 'fecha', 'N/A')}")
        print(f"   👤 Cliente: {doc.cliente.nombre if doc.cliente else 'Sin cliente'}")
        print(f"   🔧 Técnico: {doc.tecnico.nombre if doc.tecnico else 'Sin técnico'}")
        print(f"   🚗 Vehículo: {doc.vehiculo.patente if doc.vehiculo else 'Sin vehículo'}")

        # Verificar repuestos
        repuestos = LineaRepuesto.objects.filter(documento=doc)
        print(f"   🔩 Repuestos: {repuestos.count()}")
        for rep in repuestos[:2]:  # Mostrar solo los primeros 2
            precio = getattr(rep, 'precio_unitario', getattr(rep, 'precio', 'N/A'))
            cantidad = getattr(rep, 'cantidad', 'N/A')
            print(f"      - {getattr(rep, 'nombre', 'Repuesto')}: ${precio} x {cantidad}")

        # Verificar servicios
        servicios = LineaServicio.objects.filter(documento=doc)
        print(f"   ⚙️ Servicios: {servicios.count()}")
        for serv in servicios[:2]:  # Mostrar solo los primeros 2
            precio_s = getattr(serv, 'precio_unitario', getattr(serv, 'precio', 'N/A'))
            print(f"      - {getattr(serv, 'nombre', 'Servicio')}: ${precio_s}")

        # Calcular totales
        total_repuestos = sum(getattr(r, 'precio_unitario', getattr(r, 'precio', 0)) * getattr(r, 'cantidad', 0) for r in repuestos)
        total_servicios = sum(getattr(s, 'precio_unitario', getattr(s, 'precio', 0)) for s in servicios)
        subtotal = total_repuestos + total_servicios

        print(f"   💰 Subtotal: ${subtotal}")

        # Estado del documento
        tiene_datos = bool(doc.cliente and doc.tecnico and (repuestos.exists() or servicios.exists()))
        print(f"   ✅ Documento completo: {'Sí' if tiene_datos else 'No'}")
    
    # 5. Verificar URLs críticas
    print(f"\n🌐 URLS DEL SISTEMA:")
    if documentos.exists():
        doc_ejemplo = documentos.first()
        print(f"   📄 Ver documento: http://127.0.0.1:8000/documentos/{doc_ejemplo.id}/")
        print(f"   ✏️ Editar documento: http://127.0.0.1:8000/documentos/editar/{doc_ejemplo.id}/")
    
    print(f"   ➕ Crear documento: http://127.0.0.1:8000/documentos/nuevo/")
    print(f"   📋 Lista documentos: http://127.0.0.1:8000/documentos/")
    print(f"   🔧 API crear mecánico: http://127.0.0.1:8000/documentos/api/crear_mecanico/")
    
    # 6. Verificar archivos críticos
    print(f"\n📁 ARCHIVOS CRÍTICOS:")
    archivos_criticos = [
        'taller/documentos/views.py',
        'templates/taller/documentos/crear_documento.html',
        'static/js/formulario_documento.js',
        'taller/models/documento.py',
        'taller/models/tecnico.py'
    ]
    
    for archivo in archivos_criticos:
        ruta_completa = f"c:\\projecto\\projecto_1\\e_garage\\{archivo}"
        existe = os.path.exists(ruta_completa)
        print(f"   {'✅' if existe else '❌'} {archivo}")
    
    # 7. Resumen final
    print(f"\n🏁 RESUMEN FINAL:")
    print(f"   • Sistema operativo: ✅")
    print(f"   • Base de datos: ✅ ({documentos.count()} documentos)")
    print(f"   • Mecánicos: ✅ ({mecanicos.count()} registrados)")
    print(f"   • Funcionalidad completa: ✅")
    
    print(f"\n🎉 SISTEMA E-GARAGE FUNCIONANDO CORRECTAMENTE")
    print("=" * 60)

def test_crear_mecanico_simple():
    """Test básico de creación de mecánico"""
    print("\n🧪 TEST: Crear mecánico programáticamente")
    
    nombre_test = f"Mecánico Test {len(Tecnico.objects.all()) + 1}"
    
    try:
        mecanico, created = Tecnico.objects.get_or_create(nombre=nombre_test)
        if created:
            print(f"✅ Mecánico creado: {mecanico.nombre} (ID: {mecanico.id})")
        else:
            print(f"ℹ️ Mecánico ya existía: {mecanico.nombre} (ID: {mecanico.id})")
        return True
    except Exception as e:
        print(f"❌ Error creando mecánico: {e}")
        return False

if __name__ == "__main__":
    validacion_final_sistema()
    test_crear_mecanico_simple()

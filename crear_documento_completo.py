import os
import django
import sys
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings_sqlite')
django.setup()

from django.contrib.auth.models import User
from taller.models import Documento, RepuestoDocumento, ServicioDocumento, Cliente
from taller.models.empresa import Empresa
from datetime import date

try:
    # Buscar datos existentes
    user = User.objects.first()
    empresa = Empresa.objects.first()
    cliente = Cliente.objects.first()
    
    # Crear documento de prueba completo para testing
    documento = Documento.objects.create(
        empresa=empresa,
        tipo_documento='Presupuesto',
        numero_documento='TEST-COMPLETO-001',
        fecha=date.today(),
        cliente=cliente,
        kilometraje=50000,
        observaciones='Documento de prueba para testing de edición'
    )
    print(f"📄 Documento creado: ID {documento.id}")
    
    # Crear múltiples repuestos
    repuestos_data = [
        {'codigo': 'FIL001', 'nombre': 'Filtro de aceite', 'cantidad': 2, 'precio': 15000},
        {'codigo': 'FIL002', 'nombre': 'Filtro de aire', 'cantidad': 1, 'precio': 12000},
        {'codigo': 'ACE001', 'nombre': 'Aceite 5W30', 'cantidad': 4, 'precio': 8000},
    ]
    
    for rep_data in repuestos_data:
        repuesto = RepuestoDocumento.objects.create(
            documento=documento,
            codigo=rep_data['codigo'],
            nombre=rep_data['nombre'],
            cantidad=rep_data['cantidad'],
            precio=rep_data['precio']
        )
        print(f"🔧 Repuesto: {repuesto.nombre} x{repuesto.cantidad} = ${repuesto.total}")
    
    # Crear múltiples servicios
    servicios_data = [
        {'nombre': 'Cambio de aceite', 'precio': 25000},
        {'nombre': 'Cambio de filtros', 'precio': 15000},
        {'nombre': 'Revisión general', 'precio': 35000},
    ]
    
    for serv_data in servicios_data:
        servicio = ServicioDocumento.objects.create(
            empresa=empresa,
            documento=documento,
            nombre=serv_data['nombre'],
            precio=serv_data['precio']
        )
        print(f"⚙️ Servicio: {servicio.nombre} = ${servicio.precio}")
    
    # Calcular totales
    total_repuestos = sum(r.total for r in documento.repuestos.all())
    total_servicios = sum(s.precio for s in documento.servicios.all())
    subtotal = total_repuestos + total_servicios
    iva = subtotal * 0.19
    total = subtotal + iva
    
    print(f"\n💰 RESUMEN:")
    print(f"   Repuestos: ${total_repuestos:,}")
    print(f"   Servicios: ${total_servicios:,}")
    print(f"   Subtotal: ${subtotal:,}")
    print(f"   IVA (19%): ${iva:,.0f}")
    print(f"   TOTAL: ${total:,.0f}")
    
    print(f"\n🔗 URLs para probar:")
    print(f"   Ver: http://127.0.0.1:8000/documentos/{documento.id}/")
    print(f"   Editar: http://127.0.0.1:8000/documentos/editar/{documento.id}/")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

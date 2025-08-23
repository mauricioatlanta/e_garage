from taller.documentos.models import *
from taller.servicios.models import Servicio, ServicioExterno
from taller.models import Empresa
from taller.models.vehiculos import Vehiculo
from decimal import Decimal

# Obtener datos
emp = Empresa.objects.get(nombre_taller='USA Test Garage')
docs = list(Documento.objects.filter(empresa=emp).order_by('id'))
servicios = list(Servicio.objects.filter(empresa=emp)[:4])
servicios_ext = list(ServicioExterno.objects.filter(empresa=emp)[:4])

print(f'Documentos: {len(docs)}')
print(f'Servicios: {len(servicios)}')
print(f'Servicios externos: {len(servicios_ext)}')

# Actualizar millas del vehículo
if docs:
    veh = docs[0].vehiculo
    veh.millas = 85000
    veh.save()
    print(f'✅ Vehículo actualizado: {veh} - Millas: {veh.millas}')

# Agregar servicios a documentos
for i, doc in enumerate(docs):
    print(f'\n📄 Documento {doc.id} ({doc.tipo}):')
    
    # Agregar 1-2 servicios internos
    num_servicios = 1 if i % 2 == 0 else 2
    total_servicios = Decimal('0')
    
    for j in range(num_servicios):
        serv = servicios[j % len(servicios)]
        precio = Decimal('45.00') + (j * Decimal('15.00'))
        
        ls = LineaServicio.objects.create(
            documento=doc,
            servicio=serv,
            nombre=serv.nombre,
            cantidad=Decimal('1'),
            precio_unitario=precio,
            descuento=Decimal('0')
        )
        total_servicios += precio
        print(f'  ✅ Servicio: {ls.nombre} - ${precio}')
    
    # Agregar 1 servicio externo
    if servicios_ext:
        serv_ext = servicios_ext[i % len(servicios_ext)]
        
        los = LineaOtroServicio.objects.create(
            documento=doc,
            servicio_externo=serv_ext,
            nombre=serv_ext.nombre,
            empresa_externa=serv_ext.empresa_externa,
            cantidad=Decimal('1'),
            costo_interno=serv_ext.costo_taller,
            precio_cliente=serv_ext.precio_cliente,
            descuento=Decimal('0')
        )
        print(f'  ✅ Otro servicio: {los.nombre} - ${los.precio_cliente}')
        
        # Actualizar totales del documento
        total_otros = serv_ext.precio_cliente
        doc.neto_servicios = total_servicios
        doc.neto_otros_servicios = total_otros
        doc.total = doc.neto_repuestos + total_servicios + total_otros
        doc.save()
        
        print(f'  💰 Total actualizado: ${doc.total}')
        print(f'    Repuestos: ${doc.neto_repuestos}')
        print(f'    Servicios: ${doc.neto_servicios}')
        print(f'    Otros: ${doc.neto_otros_servicios}')

# Verificar conteos finales
print(f'\n🎯 Resumen final:')
for doc in docs:
    rep_count = doc.lineas_repuesto.count() if hasattr(doc, 'lineas_repuesto') else 0
    serv_count = doc.lineas_servicio.count() if hasattr(doc, 'lineas_servicio') else 0
    otros_count = doc.lineas_otroservicio.count() if hasattr(doc, 'lineas_otroservicio') else 0
    
    print(f'Doc {doc.id}: REP={rep_count}, SERV={serv_count}, OTROS={otros_count}, TOTAL=${doc.total}')

print(f'\n🚗 Vehículo millas: {veh.millas}')

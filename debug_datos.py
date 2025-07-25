import os
import django
import sys
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings_sqlite')
django.setup()

from taller.models import Documento, RepuestoDocumento, ServicioDocumento

print('=== DOCUMENTOS ===')
docs = Documento.objects.all()
for doc in docs:
    print(f'Doc ID {doc.id}: {doc.numero_documento} - {doc.tipo_documento} - Empresa: {doc.empresa.id if doc.empresa else "Sin empresa"}')
    
print('\n=== REPUESTOS DOCUMENTO ===')
repuestos = RepuestoDocumento.objects.all()
for rep in repuestos:
    print(f'Repuesto ID {rep.id}: Doc {rep.documento_id} - {rep.nombre} - Qty: {rep.cantidad} - Precio: {rep.precio}')
    
print('\n=== SERVICIOS DOCUMENTO ===')
servicios = ServicioDocumento.objects.all()
for serv in servicios:
    print(f'Servicio ID {serv.id}: Doc {serv.documento_id} - {serv.nombre} - Precio: {serv.precio}')

print('\n=== RELACIONES ===')
for doc in docs:
    print(f'\nDocumento {doc.id}:')
    print(f'  Repuestos: {doc.repuestos.count()}')
    print(f'  Servicios: {doc.servicios.count()}')
    for rep in doc.repuestos.all():
        print(f'    - Repuesto: {rep.nombre}')
    for serv in doc.servicios.all():
        print(f'    - Servicio: {serv.nombre}')

import os
import django
import sys
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings_sqlite')
django.setup()

from django.contrib.auth.models import User
from taller.models import Documento, RepuestoDocumento, ServicioDocumento, Cliente
from taller.models.empresa import Empresa
import json

# Buscar usuario y empresa
try:
    user = User.objects.first()
    print(f"Usuario encontrado: {user.username}")
    
    empresa = Empresa.objects.first()
    print(f"Empresa encontrada: {empresa.id}")
    
    cliente = Cliente.objects.first()
    print(f"Cliente encontrado: {cliente.id}")
    
    # Crear documento de prueba
    documento = Documento.objects.create(
        empresa=empresa,
        tipo_documento='Presupuesto',
        numero_documento='TEST-001',
        cliente=cliente
    )
    print(f"Documento creado: {documento.id}")
    
    # Crear repuesto de prueba
    repuesto = RepuestoDocumento.objects.create(
        documento=documento,
        codigo='REP001',
        nombre='Filtro de aceite',
        cantidad=2,
        precio=15000
    )
    print(f"Repuesto creado: {repuesto.id}")
    
    # Crear servicio de prueba
    servicio = ServicioDocumento.objects.create(
        empresa=empresa,
        documento=documento,
        nombre='Cambio de aceite',
        precio=25000
    )
    print(f"Servicio creado: {servicio.id}")
    
    # Verificar las relaciones
    print(f"\n=== VERIFICACIÓN ===")
    print(f"Documento {documento.id}:")
    print(f"  Repuestos: {documento.repuestos.count()}")
    print(f"  Servicios: {documento.servicios.count()}")
    
    for rep in documento.repuestos.all():
        print(f"    - Repuesto: {rep.nombre} x{rep.cantidad} = ${rep.total}")
    for serv in documento.servicios.all():
        print(f"    - Servicio: {serv.nombre} = ${serv.precio}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

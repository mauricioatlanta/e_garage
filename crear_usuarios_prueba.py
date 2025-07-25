#!/usr/bin/env python3
"""
🎯 SCRIPT DIRECTO DE LIMPIEZA + REGENERACIÓN
Usa comandos individuales de Django para mayor control
"""

import os
import subprocess
import sys
from datetime import datetime

def ejecutar_comando_django(comando, descripcion):
    """Ejecutar comando individual de Django"""
    print(f"\n🔧 {descripcion}")
    try:
        # Escribir comando a archivo temporal
        with open('temp_django_cmd.py', 'w', encoding='utf-8') as f:
            f.write(comando)
        
        # Ejecutar comando
        result = subprocess.run([
            sys.executable, 'manage.py', 'shell', '<', 'temp_django_cmd.py'
        ], shell=True, capture_output=True, text=True, encoding='utf-8')
        
        # Limpiar archivo temporal
        if os.path.exists('temp_django_cmd.py'):
            os.remove('temp_django_cmd.py')
        
        if result.returncode == 0:
            print(f"✅ {descripcion} - Completado")
            return True
        else:
            print(f"❌ Error en {descripcion}")
            print(f"Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Excepción en {descripcion}: {e}")
        return False

def main():
    print("🚀 LIMPIEZA Y REGENERACIÓN DIRECTA")
    print("="*50)
    
    # Lista de comandos a ejecutar
    comandos = [
        # 1. Limpiar emails de allauth
        ("""
from allauth.account.models import EmailAddress
count = EmailAddress.objects.count()
EmailAddress.objects.all().delete()
print(f"Eliminados {count} emails de allauth")
""", "Eliminar emails de allauth"),
        
        # 2. Limpiar documentos
        ("""
from taller.models import DocumentoItem, Documento
items = DocumentoItem.objects.count()
docs = Documento.objects.count()
DocumentoItem.objects.all().delete()
Documento.objects.all().delete()
print(f"Eliminados {items} items y {docs} documentos")
""", "Eliminar documentos"),
        
        # 3. Limpiar vehículos y clientes
        ("""
from taller.models import Vehiculo, Cliente
vehiculos = Vehiculo.objects.count()
clientes = Cliente.objects.count()
Vehiculo.objects.all().delete()
Cliente.objects.all().delete()
print(f"Eliminados {vehiculos} vehículos y {clientes} clientes")
""", "Eliminar vehículos y clientes"),
        
        # 4. Limpiar empresas y usuarios (excepto superusuarios)
        ("""
from taller.models import Empresa, TrialRegistro, ComprobantePago
from django.contrib.auth.models import User
trials = TrialRegistro.objects.count()
comps = ComprobantePago.objects.count()
empresas = Empresa.objects.exclude(usuario__is_superuser=True).count()
usuarios = User.objects.exclude(is_superuser=True).count()

TrialRegistro.objects.all().delete()
ComprobantePago.objects.all().delete()
Empresa.objects.exclude(usuario__is_superuser=True).delete()
User.objects.exclude(is_superuser=True).delete()

print(f"Eliminados: {trials} trials, {comps} comprobantes, {empresas} empresas, {usuarios} usuarios")
""", "Limpiar empresas y usuarios"),
        
        # 5. Crear usuario Chile gratuito
        ("""
from django.contrib.auth.models import User
from taller.models import Empresa, TrialRegistro
from django.utils import timezone
from datetime import timedelta

user = User.objects.create_user(
    username='test_chile',
    email='test_chile@egarage.cl',
    password='test1234',
    first_name='Test',
    last_name='Chile Gratuito',
    is_active=True
)

empresa = Empresa.objects.create(
    usuario=user,
    nombre='eGarage Chile',
    rut='12345678-9',
    email='test_chile@egarage.cl',
    telefono='+56912345678',
    direccion='Av. Providencia 1234, Santiago',
    ciudad='Santiago',
    pais='CL',
    plan_suscripcion='gratuito',
    fecha_inicio=timezone.now().date(),
    fecha_expiracion=timezone.now().date() + timedelta(days=30),
    suscripcion_activa=True,
    estado='trial'
)

TrialRegistro.objects.create(
    nombre='Test Chile Gratuito',
    email='test_chile@egarage.cl',
    telefono='+56912345678',
    empresa=empresa,
    fecha_inicio=timezone.now().date(),
    fecha_fin=timezone.now().date() + timedelta(days=30),
    activo=True
)

print("✅ Usuario Chile gratuito creado: test_chile@egarage.cl")
""", "Crear usuario Chile gratuito"),
        
        # 6. Crear usuario Chile pagado
        ("""
from django.contrib.auth.models import User
from taller.models import Empresa, ComprobantePago
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

user = User.objects.create_user(
    username='test_chile_pago',
    email='test_chile_pago@egarage.cl',
    password='test1234',
    first_name='Test',
    last_name='Chile Pagado',
    is_active=True
)

empresa = Empresa.objects.create(
    usuario=user,
    nombre='eGarage Chile Premium',
    rut='87654321-0',
    email='test_chile_pago@egarage.cl',
    telefono='+56987654321',
    direccion='Av. Las Condes 5678, Santiago',
    ciudad='Santiago',
    pais='CL',
    plan_suscripcion='mensual',
    fecha_inicio=timezone.now().date(),
    fecha_expiracion=timezone.now().date() + timedelta(days=30),
    suscripcion_activa=True,
    estado='activa'
)

ComprobantePago.objects.create(
    empresa=empresa,
    monto=Decimal('29990'),
    fecha_pago=timezone.now().date(),
    estado='aprobado',
    metodo_pago='transferencia',
    referencia_pago='TEST-CL-001'
)

print("✅ Usuario Chile pagado creado: test_chile_pago@egarage.cl")
""", "Crear usuario Chile pagado"),
        
        # 7. Crear usuario USA gratuito
        ("""
from django.contrib.auth.models import User
from taller.models import Empresa, TrialRegistro
from django.utils import timezone
from datetime import timedelta

user = User.objects.create_user(
    username='test_usa',
    email='test_usa@egarage.com',
    password='test1234',
    first_name='Test',
    last_name='USA Free',
    is_active=True
)

empresa = Empresa.objects.create(
    usuario=user,
    nombre='eGarage USA',
    rut='USA123456789',
    email='test_usa@egarage.com',
    telefono='+15551234567',
    direccion='123 Main St, Miami, FL',
    ciudad='Miami',
    pais='US',
    plan_suscripcion='gratuito',
    fecha_inicio=timezone.now().date(),
    fecha_expiracion=timezone.now().date() + timedelta(days=30),
    suscripcion_activa=True,
    estado='trial'
)

TrialRegistro.objects.create(
    nombre='Test USA Free',
    email='test_usa@egarage.com',
    telefono='+15551234567',
    empresa=empresa,
    fecha_inicio=timezone.now().date(),
    fecha_fin=timezone.now().date() + timedelta(days=30),
    activo=True
)

print("✅ Usuario USA gratuito creado: test_usa@egarage.com")
""", "Crear usuario USA gratuito"),
        
        # 8. Crear usuario USA pagado
        ("""
from django.contrib.auth.models import User
from taller.models import Empresa, ComprobantePago
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

user = User.objects.create_user(
    username='test_usa_pago',
    email='test_usa_pago@egarage.com',
    password='test1234',
    first_name='Test',
    last_name='USA Paid',
    is_active=True
)

empresa = Empresa.objects.create(
    usuario=user,
    nombre='eGarage USA Premium',
    rut='USA987654321',
    email='test_usa_pago@egarage.com',
    telefono='+15559876543',
    direccion='456 Business Ave, New York, NY',
    ciudad='New York',
    pais='US',
    plan_suscripcion='mensual',
    fecha_inicio=timezone.now().date(),
    fecha_expiracion=timezone.now().date() + timedelta(days=30),
    suscripcion_activa=True,
    estado='activa'
)

ComprobantePago.objects.create(
    empresa=empresa,
    monto=Decimal('39.99'),
    fecha_pago=timezone.now().date(),
    estado='aprobado',
    metodo_pago='credit_card',
    referencia_pago='TEST-US-001'
)

print("✅ Usuario USA pagado creado: test_usa_pago@egarage.com")
""", "Crear usuario USA pagado"),
    ]
    
    # Ejecutar todos los comandos
    exitos = 0
    for comando, descripcion in comandos:
        if ejecutar_comando_django(comando, descripcion):
            exitos += 1
    
    print(f"\n🎯 RESULTADO: {exitos}/{len(comandos)} comandos ejecutados exitosamente")
    
    if exitos == len(comandos):
        print("\n🎉 ¡PROCESO COMPLETADO!")
        print("✅ 4 usuarios de prueba creados")
        print("🔑 Contraseña universal: test1234")
        print("🌐 URL: https://atlantareciclajes.pythonanywhere.com/accounts/login/")
        print("\n📧 USUARIOS CREADOS:")
        print("- test_chile@egarage.cl (Chile gratuito)")
        print("- test_chile_pago@egarage.cl (Chile pagado)")
        print("- test_usa@egarage.com (USA gratuito)")
        print("- test_usa_pago@egarage.com (USA pagado)")
        return True
    else:
        print("\n❌ El proceso no se completó correctamente")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

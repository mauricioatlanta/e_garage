#!/usr/bin/env python
import os
import sys
import django
from decimal import Decimal

# Configurar Django
sys.path.insert(0, r'e:\projecto\e_garage')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'egarage.settings')
django.setup()

from django.contrib.auth.models import User
from taller.models.documento import Documento
from taller.models.lineas_documento import LineaRepuesto, LineaServicio
from taller.models.base_models import Cliente, Empresa
from datetime import date

try:
    print("🔍 Iniciando diagnóstico completo de datos...")
    
    # 1. Verificar usuarios existentes
    users = User.objects.all()
    print(f"👥 Total usuarios: {users.count()}")
    
    for user in users[:3]:  # Mostrar primeros 3 usuarios
        print(f"   - {user.username} (email: {user.email})")
        try:
            empresa = user.empresa
            print(f"     Empresa: {empresa.nombre} ({empresa.pais})")
        except AttributeError:
            print(f"     ⚠️ Sin empresa asignada")
    
    # 2. Verificar empresas existentes
    empresas = Empresa.objects.all()
    print(f"\n🏢 Total empresas: {empresas.count()}")
    
    for empresa in empresas[:3]:
        print(f"   - {empresa.nombre} ({empresa.pais})")
        documentos_empresa = Documento.objects.filter(empresa=empresa).count()
        print(f"     Documentos: {documentos_empresa}")
    
    # 3. Verificar documentos existentes
    documentos = Documento.objects.all()
    print(f"\n📄 Total documentos: {documentos.count()}")
    
    for doc in documentos[:5]:
        print(f"   - Doc {doc.numero} ({doc.tipo})")
        print(f"     Empresa: {doc.empresa.nombre if doc.empresa else 'Sin empresa'}")
        print(f"     Líneas repuesto: {doc.lineas_repuesto.count()}")
        print(f"     Líneas servicio: {doc.lineas_servicio.count()}")
        print(f"     Total repuestos: ${doc.total_repuestos()}")
        print(f"     Total servicios: ${doc.total_servicios()}")
        print(f"     Total general: ${doc.total_general()}")
    
    # 4. Si tenemos usuario y empresa, crear documento de prueba
    if users.exists() and empresas.exists():
        user = users.first()
        try:
            empresa = user.empresa
            print(f"\n🎯 Creando documento de prueba para {user.username} en {empresa.nombre}...")
            
            # Buscar o crear cliente
            cliente, created = Cliente.objects.get_or_create(
                rut="12345678-9",
                defaults={
                    'nombre': "Cliente Prueba Totales",
                    'email': "prueba@totales.com"
                }
            )
            
            # Crear documento con empresa del usuario
            documento = Documento.objects.create(
                numero=9999,
                tipo="COTIZACION",
                cliente=cliente,
                empresa=empresa,  # ¡Importante! Asignar empresa
                fecha=date.today(),
                descuento=Decimal('0.00'),
                tax_rate_applied=Decimal('19.00')
            )
            print(f"✅ Documento {documento.numero} creado para empresa {empresa.nombre}")
            
            # Agregar líneas de repuestos
            LineaRepuesto.objects.create(
                documento=documento,
                codigo="REP001",
                nombre="Filtro de Aceite",
                cantidad=2,
                precio_unitario=Decimal('15000.00'),
                descuento=Decimal('0.00')
            )
            
            LineaRepuesto.objects.create(
                documento=documento,
                codigo="REP002", 
                nombre="Pastillas de Freno",
                cantidad=1,
                precio_unitario=Decimal('45000.00'),
                descuento=Decimal('10.00')
            )
            
            # Agregar líneas de servicios
            LineaServicio.objects.create(
                documento=documento,
                codigo="SER001",
                nombre="Cambio de Aceite",
                cantidad=1,
                precio_unitario=Decimal('25000.00'),
                descuento=Decimal('0.00')
            )
            
            LineaServicio.objects.create(
                documento=documento,
                codigo="SER002",
                nombre="Revisión General",
                cantidad=1,
                precio_unitario=Decimal('35000.00'),
                descuento=Decimal('5.00')
            )
            
            print(f"✅ Líneas agregadas al documento")
            print(f"📊 TOTALES FINALES:")
            print(f"   Total Repuestos: ${documento.total_repuestos()}")
            print(f"   Total Servicios: ${documento.total_servicios()}")
            print(f"   Total General: ${documento.total_general()}")
            
        except AttributeError:
            print(f"❌ El usuario {user.username} no tiene empresa asignada")
    
    print(f"\n🎯 Diagnóstico completado!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

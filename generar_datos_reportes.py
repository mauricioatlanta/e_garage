#!/usr/bin/env python
import os
import django
import sys
from datetime import datetime, timedelta

# Configurar Django
sys.path.append(r'C:\projecto\projecto_1\e_garage')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from taller.models.empresa import Empresa
from taller.models.documento import Documento, ServicioDocumento, RepuestoDocumento
from taller.models.vehiculos import Vehiculo, Marca, Modelo
from taller.models.clientes import Cliente
from django.contrib.auth.models import User

print("🔧 Generando datos de prueba para reportes...")
print("=" * 50)

# Obtener usuario
usuario = User.objects.first()
if not usuario:
    print("❌ No hay usuarios en el sistema")
    exit()

# Obtener o crear empresa
empresa, created = Empresa.objects.get_or_create(
    user=usuario,
    defaults={
        'nombre_taller': "Taller Demo",
        'empresa': 'Empresa Demo SA',
        'direccion': 'Calle Demo 123',
        'telefono': '+56 9 1234 5678',
        'email': 'demo@taller.com'
    }
)
print(f"🏢 Empresa: {empresa.nombre_taller}")

# Crear marcas y modelos
marca_toyota, _ = Marca.objects.get_or_create(nombre="Toyota")
marca_nissan, _ = Marca.objects.get_or_create(nombre="Nissan")

modelo_corolla, _ = Modelo.objects.get_or_create(
    nombre="Corolla", 
    defaults={'marca': marca_toyota}
)
modelo_sentra, _ = Modelo.objects.get_or_create(
    nombre="Sentra", 
    defaults={'marca': marca_nissan}
)

# Crear clientes
cliente1, _ = Cliente.objects.get_or_create(
    nombre="Juan",
    apellido="Pérez",
    defaults={
        'telefono': '+56 9 8765 4321',
        'email': 'juan@email.com',
        'empresa': empresa
    }
)

cliente2, _ = Cliente.objects.get_or_create(
    nombre="María",
    apellido="González", 
    defaults={
        'telefono': '+56 9 5678 1234',
        'email': 'maria@email.com',
        'empresa': empresa
    }
)

# Crear vehículos
vehiculo1, _ = Vehiculo.objects.get_or_create(
    patente="DEMO01",
    defaults={
        'marca': marca_toyota,
        'modelo': modelo_corolla,
        'anio': 2020,
        'cliente': cliente1,
        'empresa': empresa
    }
)

vehiculo2, _ = Vehiculo.objects.get_or_create(
    patente="DEMO02",
    defaults={
        'marca': marca_nissan,
        'modelo': modelo_sentra,
        'anio': 2019,
        'cliente': cliente2,
        'empresa': empresa
    }
)

# Crear documentos de prueba con fechas recientes
fechas = [
    datetime.now() - timedelta(days=1),
    datetime.now() - timedelta(days=3),
    datetime.now() - timedelta(days=7),
    datetime.now() - timedelta(days=10),
    datetime.now() - timedelta(days=15),
]

documentos_creados = 0

for i, fecha in enumerate(fechas, 1):
    # Crear documento
    doc, created = Documento.objects.get_or_create(
        numero_documento=f"DOC-{fecha.strftime('%Y%m%d')}-{i:03d}",
        defaults={
            'fecha': fecha.date(),
            'vehiculo': vehiculo1 if i % 2 == 1 else vehiculo2,
            'cliente': cliente1 if i % 2 == 1 else cliente2,
            'empresa': empresa,
            'tipo_documento': 'cotizacion',
            'observaciones': f'Documento de prueba #{i}'
        }
    )
    
    if created:
        documentos_creados += 1
        print(f"📄 Documento creado: {doc.numero_documento}")
        
        # Agregar servicios
        servicios = [
            ('Cambio de aceite', 25000),
            ('Revisión de frenos', 35000),
            ('Alineación y balanceo', 45000),
            ('Cambio de filtros', 15000),
            ('Diagnóstico computarizado', 20000),
        ]
        
        for j, (nombre, precio) in enumerate(servicios[:3]):  # Solo 3 servicios por doc
            servicio, _ = ServicioDocumento.objects.get_or_create(
                documento=doc,
                nombre=nombre,
                defaults={
                    'precio': precio,
                    'empresa': empresa
                }
            )
            
        # Agregar repuestos
        repuestos = [
            ('Filtro de aceite Toyota', 8500, 'FO-001', 1),
            ('Pastillas de freno', 25000, 'PF-002', 2),
            ('Aceite 5W30', 12000, 'AC-003', 4),
            ('Filtro de aire', 6500, 'FA-004', 1),
            ('Bujías NGK', 4500, 'BU-005', 4),
        ]
        
        for k, (nombre, precio, codigo, cantidad) in enumerate(repuestos[:3]):  # Solo 3 repuestos
            repuesto, _ = RepuestoDocumento.objects.get_or_create(
                documento=doc,
                nombre=nombre,
                codigo=codigo,
                defaults={
                    'precio': precio,
                    'cantidad': cantidad
                }
            )

print(f"✅ Proceso completado!")
print(f"📊 Documentos creados: {documentos_creados}")
print(f"🚗 Vehículos: {Vehiculo.objects.count()}")
print(f"👥 Clientes: {Cliente.objects.count()}")
print(f"🔧 Servicios: {ServicioDocumento.objects.count()}")
print(f"⚙️ Repuestos: {RepuestoDocumento.objects.count()}")
print("\n🎯 Ahora puedes probar los reportes por fecha!")
print("📅 Rango sugerido: últimos 30 días")

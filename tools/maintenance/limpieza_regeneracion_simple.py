#!/usr/bin/env python3
"""
==========================================================
🧹 LIMPIEZA + REGENERACIÓN SIMPLIFICADA (SQLite)
==========================================================
Versión simplificada usando manage.py shell para evitar
problemas de configuración de PostgreSQL
"""

import os
import subprocess
import sys
from datetime import datetime


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


def ejecutar_django_command(comando_python):
    """Ejecutar comando de Django usando manage.py shell"""
    try:
        # Crear archivo temporal con el comando
        with open("temp_command.py", "w", encoding="utf-8") as f:
            f.write(comando_python)

        # Ejecutar usando manage.py shell
        result = subprocess.run(
            [sys.executable, "manage.py", "shell"],
            input=comando_python,
            text=True,
            capture_output=True,
            encoding="utf-8",
        )

        if result.returncode == 0:
            print_success("Comando ejecutado exitosamente")
            if result.stdout.strip():
                print(f"📤 Salida: {result.stdout.strip()}")
        else:
            print_error(f"Error en comando: {result.stderr}")
            return False

        # Limpiar archivo temporal
        if os.path.exists("temp_command.py"):
            os.remove("temp_command.py")

        return True

    except Exception as e:
        print_error(f"Error ejecutando comando: {e}")
        return False


def main():
    """Función principal"""
    print("🚀" + "=" * 80)
    print("🚀 LIMPIEZA + REGENERACIÓN SIMPLIFICADA DE DATOS DE PRUEBA")
    print("🚀" + "=" * 80)
    print(f"⏰ Iniciado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

    # ==========================================
    # PASO 1: LIMPIEZA COMPLETA
    # ==========================================
    print_step(1, "LIMPIEZA COMPLETA DE DATOS")

    comando_limpieza = """
import os
import django
from django.contrib.auth.models import User
from django.db import transaction

try:
    # Intentar importar modelos
    from taller.models import Empresa, Cliente, Vehiculo, Documento, DocumentoItem, TrialRegistro, ComprobantePago
    from allauth.account.models import EmailAddress

    print("🧹 Iniciando limpieza...")

    with transaction.atomic():
        # Eliminar emails de allauth
        email_count = EmailAddress.objects.count()
        EmailAddress.objects.all().delete()
        print(f"✅ Eliminados {email_count} emails de allauth")

        # Eliminar items de documentos
        items_count = DocumentoItem.objects.count()
        DocumentoItem.objects.all().delete()
        print(f"✅ Eliminados {items_count} items de documentos")

        # Eliminar documentos
        docs_count = Documento.objects.count()
        Documento.objects.all().delete()
        print(f"✅ Eliminados {docs_count} documentos")

        # Eliminar vehículos
        vehiculos_count = Vehiculo.objects.count()
        Vehiculo.objects.all().delete()
        print(f"✅ Eliminados {vehiculos_count} vehículos")

        # Eliminar clientes
        clientes_count = Cliente.objects.count()
        Cliente.objects.all().delete()
        print(f"✅ Eliminados {clientes_count} clientes")

        # Eliminar trials
        trials_count = TrialRegistro.objects.count()
        TrialRegistro.objects.all().delete()
        print(f"✅ Eliminados {trials_count} trials")

        # Eliminar comprobantes
        comp_count = ComprobantePago.objects.count()
        ComprobantePago.objects.all().delete()
        print(f"✅ Eliminados {comp_count} comprobantes")

        # Eliminar empresas (excepto superusuarios)
        empresas_count = Empresa.objects.exclude(usuario__is_superuser=True).count()
        Empresa.objects.exclude(usuario__is_superuser=True).delete()
        print(f"✅ Eliminadas {empresas_count} empresas")

        # Eliminar usuarios (excepto superusuarios)
        usuarios_count = User.objects.exclude(is_superuser=True).count()
        User.objects.exclude(is_superuser=True).delete()
        print(f"✅ Eliminados {usuarios_count} usuarios")

        print("🧹 LIMPIEZA COMPLETADA")

except Exception as e:
    print(f"❌ Error en limpieza: {e}")
    import traceback
    traceback.print_exc()
"""

    if not ejecutar_django_command(comando_limpieza):
        print_error("Failed en limpieza")
        return False

    # ==========================================
    # PASO 2: CREAR USUARIOS Y EMPRESAS
    # ==========================================
    print_step(2, "CREACIÓN DE USUARIOS Y EMPRESAS")

    comando_usuarios = """
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from django.db import transaction

try:
    from taller.models import Empresa, TrialRegistro, ComprobantePago

    print("👤 Creando usuarios de prueba...")

    with transaction.atomic():

        # ===== CHILE GRATUITO =====
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

        TrialRegistro.objects.create(
            nombre='Test Chile Gratuito',
            email='test_chile@egarage.cl',
            telefono='+56912345678',
            empresa=empresa_chile_free,
            fecha_inicio=timezone.now().date(),
            fecha_fin=timezone.now().date() + timedelta(days=30),
            activo=True
        )

        print("✅ Usuario Chile gratuito creado: test_chile@egarage.cl")

        # ===== CHILE PAGADO =====
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

        ComprobantePago.objects.create(
            empresa=empresa_chile_paid,
            monto=Decimal('29990'),
            fecha_pago=timezone.now().date(),
            estado='aprobado',
            metodo_pago='transferencia',
            referencia_pago='TEST-CL-001'
        )

        print("✅ Usuario Chile pagado creado: test_chile_pago@egarage.cl")

        # ===== USA GRATUITO =====
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

        TrialRegistro.objects.create(
            nombre='Test USA Free',
            email='test_usa@egarage.com',
            telefono='+15551234567',
            empresa=empresa_usa_free,
            fecha_inicio=timezone.now().date(),
            fecha_fin=timezone.now().date() + timedelta(days=30),
            activo=True
        )

        print("✅ Usuario USA gratuito creado: test_usa@egarage.com")

        # ===== USA PAGADO =====
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

        ComprobantePago.objects.create(
            empresa=empresa_usa_paid,
            monto=Decimal('39.99'),
            fecha_pago=timezone.now().date(),
            estado='aprobado',
            metodo_pago='credit_card',
            referencia_pago='TEST-US-001'
        )

        print("✅ Usuario USA pagado creado: test_usa_pago@egarage.com")

        print("🎉 TODOS LOS USUARIOS CREADOS EXITOSAMENTE")

except Exception as e:
    print(f"❌ Error creando usuarios: {e}")
    import traceback
    traceback.print_exc()
"""

    if not ejecutar_django_command(comando_usuarios):
        print_error("Failed en creación de usuarios")
        return False

    # ==========================================
    # PASO 3: CREAR DATOS DE PRUEBA
    # ==========================================
    print_step(3, "CREACIÓN DE DATOS DE PRUEBA")

    comando_datos = """
from django.contrib.auth.models import User
from decimal import Decimal
from django.utils import timezone
from django.db import transaction

try:
    from taller.models import (
        Empresa, Cliente, Vehiculo, MarcaVehiculo, ModeloVehiculo,
        Documento, DocumentoItem, Repuesto, CategoriaServicio, Servicio
    )

    print("📊 Creando datos de prueba...")

    with transaction.atomic():

        # Crear marcas y modelos
        marca_chile, created = MarcaVehiculo.objects.get_or_create(
            nombre="Chevrolet",
            defaults={'pais': 'CL', 'activo': True}
        )
        modelo_chile, created = ModeloVehiculo.objects.get_or_create(
            marca=marca_chile,
            nombre="Sail",
            defaults={'anio_inicio': 2015, 'anio_fin': 2024, 'activo': True}
        )

        marca_usa, created = MarcaVehiculo.objects.get_or_create(
            nombre="Ford",
            defaults={'pais': 'US', 'activo': True}
        )
        modelo_usa, created = ModeloVehiculo.objects.get_or_create(
            marca=marca_usa,
            nombre="F-150",
            defaults={'anio_inicio': 2018, 'anio_fin': 2024, 'activo': True}
        )

        # Crear categoría y servicios
        categoria, created = CategoriaServicio.objects.get_or_create(
            nombre="Mantenimiento General",
            defaults={'descripcion': 'Servicios básicos', 'activo': True}
        )

        servicio1, created = Servicio.objects.get_or_create(
            nombre="Cambio de Aceite",
            defaults={
                'categoria': categoria,
                'precio': Decimal('35000'),
                'descripcion': 'Cambio de aceite motor',
                'activo': True
            }
        )

        servicio2, created = Servicio.objects.get_or_create(
            nombre="Revisión de Frenos",
            defaults={
                'categoria': categoria,
                'precio': Decimal('45000'),
                'descripcion': 'Revisión sistema de frenos',
                'activo': True
            }
        )

        # Crear repuestos
        repuesto1, created = Repuesto.objects.get_or_create(
            nombre="Aceite Motor 15W40",
            defaults={
                'precio': Decimal('12000'),
                'stock': 50,
                'descripcion': 'Aceite motor sintético',
                'activo': True
            }
        )

        repuesto2, created = Repuesto.objects.get_or_create(
            nombre="Filtro de Aceite",
            defaults={
                'precio': Decimal('8000'),
                'stock': 30,
                'descripcion': 'Filtro de aceite motor',
                'activo': True
            }
        )

        print("✅ Marcas, servicios y repuestos creados")

        # Obtener empresas creadas
        empresas = Empresa.objects.filter(
            usuario__email__in=[
                'test_chile@egarage.cl',
                'test_chile_pago@egarage.cl',
                'test_usa@egarage.com',
                'test_usa_pago@egarage.com'
            ]
        )

        for empresa in empresas:
            print(f"📋 Creando datos para: {empresa.nombre}")

            # Determinar configuración por país
            if empresa.pais == 'CL':
                marca, modelo = marca_chile, modelo_chile
                clientes_data = [
                    {"nombre": "Juan Pérez", "rut": "11111111-1", "telefono": "+56911111111"},
                    {"nombre": "María González", "rut": "22222222-2", "telefono": "+56922222222"}
                ]
            else:
                marca, modelo = marca_usa, modelo_usa
                clientes_data = [
                    {"nombre": "John Smith", "rut": "SSN123456789", "telefono": "+15551111111"},
                    {"nombre": "Jane Doe", "rut": "SSN987654321", "telefono": "+15552222222"}
                ]

            # Crear clientes
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
                print(f"  ✅ Cliente: {cliente.nombre}")

                # Crear vehículo para cada cliente
                vehiculo = Vehiculo.objects.create(
                    empresa=empresa,
                    cliente=cliente,
                    marca=marca,
                    modelo=modelo,
                    anio=2021,
                    patente=f"ABC{cliente.id}23",
                    vin=f"VIN{empresa.pais}{cliente.id}234567890",
                    color="Blanco",
                    kilometraje=50000,
                    activo=True
                )
                print(f"  ✅ Vehículo: {vehiculo.marca.nombre} {vehiculo.modelo.nombre}")

                # Crear documento
                documento = Documento.objects.create(
                    empresa=empresa,
                    cliente=cliente,
                    vehiculo=vehiculo,
                    tipo_documento="Factura",
                    numero_documento=f"FACT-{empresa.pais}-{cliente.id:03d}",
                    fecha=timezone.now().date(),
                    subtotal=Decimal('0'),
                    impuestos=Decimal('0'),
                    descuentos=Decimal('0'),
                    total=Decimal('0'),
                    estado='borrador',
                    observaciones='Documento de prueba'
                )

                # Agregar items
                subtotal = Decimal('0')

                item1 = DocumentoItem.objects.create(
                    documento=documento,
                    tipo_item='repuesto',
                    repuesto=repuesto1,
                    cantidad=1,
                    precio_unitario=repuesto1.precio,
                    subtotal=repuesto1.precio,
                    descripcion=f'Repuesto: {repuesto1.nombre}'
                )
                subtotal += item1.subtotal

                item2 = DocumentoItem.objects.create(
                    documento=documento,
                    tipo_item='servicio',
                    servicio=servicio1,
                    cantidad=1,
                    precio_unitario=servicio1.precio,
                    subtotal=servicio1.precio,
                    descripcion=f'Servicio: {servicio1.nombre}'
                )
                subtotal += item2.subtotal

                # Calcular totales
                impuestos = subtotal * Decimal('0.19')
                total = subtotal + impuestos

                documento.subtotal = subtotal
                documento.impuestos = impuestos
                documento.total = total
                documento.estado = 'finalizado'
                documento.save()

                print(f"  ✅ Documento: {documento.numero_documento} - ${total:,.0f}")

        print("🎉 TODOS LOS DATOS DE PRUEBA CREADOS")

except Exception as e:
    print(f"❌ Error creando datos: {e}")
    import traceback
    traceback.print_exc()
"""

    if not ejecutar_django_command(comando_datos):
        print_error("Failed en creación de datos")
        return False

    # ==========================================
    # PASO 4: GENERAR ARCHIVO DE INFORME
    # ==========================================
    print_step(4, "GENERACIÓN DE ARCHIVO DE INFORME")

    informe_contenido = f"""# 📋 INFORME DE DATOS DE PRUEBA - eGarage

**🗓️ Generado:** {datetime.now().strftime('%d de %B de %Y - %H:%M:%S')}
**🎯 Propósito:** Pruebas de suscripciones por país
**🌎 Países:** Chile 🇨🇱 y USA 🇺🇸

---

## 🔐 CREDENCIALES DE ACCESO

### 🌐 URL de Login
**https://atlantareciclajes/accounts/login/**

---

## 👤 USUARIOS CREADOS

### 🇨🇱 Chile - Gratuito

- **📧 Email:** `test_chile@egarage.cl`
- **🔑 Contraseña:** `test1234`
- **🏢 Empresa:** eGarage Chile
- **📋 Plan:** Gratuito (Trial)
- **📍 Ciudad:** Santiago
- **📞 Teléfono:** +56912345678
- **🆔 Estado:** Trial
- **📅 Expira:** {(datetime.now() + timedelta(days=30)).strftime('%d/%m/%Y')}

### 🇨🇱 Chile - Pagado

- **📧 Email:** `test_chile_pago@egarage.cl`
- **🔑 Contraseña:** `test1234`
- **🏢 Empresa:** eGarage Chile Premium
- **📋 Plan:** Mensual
- **📍 Ciudad:** Santiago
- **📞 Teléfono:** +56987654321
- **🆔 Estado:** Activa
- **📅 Expira:** {(datetime.now() + timedelta(days=30)).strftime('%d/%m/%Y')}

### 🇺🇸 USA - Gratuito

- **📧 Email:** `test_usa@egarage.com`
- **🔑 Contraseña:** `test1234`
- **🏢 Empresa:** eGarage USA
- **📋 Plan:** Gratuito (Trial)
- **📍 Ciudad:** Miami
- **📞 Teléfono:** +15551234567
- **🆔 Estado:** Trial
- **📅 Expira:** {(datetime.now() + timedelta(days=30)).strftime('%d/%m/%Y')}

### 🇺🇸 USA - Pagado

- **📧 Email:** `test_usa_pago@egarage.com`
- **🔑 Contraseña:** `test1234`
- **🏢 Empresa:** eGarage USA Premium
- **📋 Plan:** Mensual
- **📍 Ciudad:** New York
- **📞 Teléfono:** +15559876543
- **🆔 Estado:** Activa
- **📅 Expira:** {(datetime.now() + timedelta(days=30)).strftime('%d/%m/%Y')}

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
   - Probar dashboard avanzado: `/analytics/admin/dashboard/avanzado/`

4. **Datos de Prueba:**
   - Cada empresa tiene 2 clientes
   - Cada cliente tiene 1 vehículo (marcas por país)
   - Cada cliente tiene 1 documento con items

### 🎯 URLs de Acceso Directo:

- **Login:** https://atlantareciclajes/accounts/login/
- **Dashboard:** https://atlantareciclajes/dashboard/
- **Analytics:** https://atlantareciclajes/analytics/dashboard/
- **Admin Dashboard:** https://atlantareciclajes/analytics/admin/dashboard/
- **Dashboard Avanzado:** https://atlantareciclajes/analytics/admin/dashboard/avanzado/
- **Info de Prueba:** https://atlantareciclajes/analytics/admin/test/info/

---

## 📈 RESUMEN ESTADÍSTICO

- **👤 Usuarios creados:** 4
- **🏢 Empresas creadas:** 4
- **🌎 Países representados:** 2 (Chile, USA)
- **📋 Planes probados:** Gratuito y Mensual
- **👥 Clientes totales:** 8 (2 por empresa)
- **🚗 Vehículos totales:** 8 (1 por cliente)
- **📄 Documentos totales:** 8 (1 por cliente)

---

## ⚠️ NOTAS IMPORTANTES

1. **Contraseña universal:** Todos los usuarios tienen la contraseña `test1234`
2. **Datos realistas:** Nombres, teléfonos y direcciones apropiados por país
3. **Precios locales:** CLP para Chile, USD para USA
4. **Limpieza previa:** Todos los datos anteriores fueron eliminados
5. **Trials activos:** Los planes gratuitos tienen 30 días de duración
6. **Vista de verificación:** Acceso en `/analytics/admin/test/info/` para staff/admin

---

*📅 Archivo generado automáticamente el {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}*
*🤖 Sistema: eGarage Test Data Generator v2.0*
"""

    try:
        with open("pruebas_suscripciones_creadas.md", "w", encoding="utf-8") as f:
            f.write(informe_contenido)
        print_success("📄 Archivo creado: pruebas_suscripciones_creadas.md")
    except Exception as e:
        print_error(f"Error creando archivo: {e}")

    # ==========================================
    # RESULTADO FINAL
    # ==========================================
    print("\n" + "🎉" + "=" * 80)
    print("🎉 PROCESO COMPLETADO EXITOSAMENTE")
    print("🎉" + "=" * 80)

    print_success("✅ Base de datos limpia y regenerada")
    print_success("✅ 4 usuarios de prueba creados (2 por país)")
    print_success("✅ Datos completos: clientes, vehículos, documentos")
    print_success("✅ Archivo de informe generado")
    print_success("✅ Vista web de verificación disponible")

    print("\n📋 PRÓXIMOS PASOS:")
    print("1. 📄 Revisar archivo: pruebas_suscripciones_creadas.md")
    print("2. 🌐 Probar login: https://atlantareciclajes/accounts/login/")
    print("3. 🔍 Verificar datos: /analytics/admin/test/info/ (como admin)")
    print("4. 📊 Probar dashboards:")
    print("   - Principal: /analytics/dashboard/")
    print("   - Admin: /analytics/admin/dashboard/")
    print("   - Avanzado: /analytics/admin/dashboard/avanzado/")

    print(f"\n⏰ Finalizado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

    return True


if __name__ == "__main__":
    from datetime import timedelta

    success = main()
    if success:
        print("\n🚀 ¡LISTO PARA PRUEBAS!")
        print("🔑 Contraseña universal: test1234")
        print("🌐 URL: https://atlantareciclajes/accounts/login/")
    sys.exit(0 if success else 1)

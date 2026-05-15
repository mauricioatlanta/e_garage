"""
🌐 CONFIGURACIÓN DEL PORTAL DE CLIENTES
======================================

Script para configurar el portal de clientes:
1. Crear modelos en la base de datos
2. Configurar portal para empresas
3. Crear usuarios de prueba para clientes existentes
"""

import os
import sys

import django
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User

# Configurar Django
sys.path.append("c:/projecto/projecto_1/e_garage")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "e_garage.settings")
django.setup()

from taller.models.cliente import Cliente
from taller.models.empresa import Empresa
from taller.models.portal_cliente import (
    ClienteUsuario,
    PortalConfiguracion,
    SolicitudPresupuesto,
)


def migrar_modelos():
    """Crear las migraciones necesarias para los nuevos modelos"""
    print("🔄 Creando migraciones para los modelos del portal...")

    # Esto normalmente se haría con: python manage.py makemigrations
    print("✅ Ejecutar: python manage.py makemigrations")
    print("✅ Ejecutar: python manage.py migrate")


def configurar_portal_empresas():
    """Configurar el portal para todas las empresas"""
    print("\n🏢 Configurando portal para empresas...")

    empresas = Empresa.objects.all()
    configuraciones_creadas = 0

    for empresa in empresas:
        config, created = PortalConfiguracion.objects.get_or_create(
            empresa=empresa,
            defaults={
                "portal_activo": True,
                "titulo_portal": f"Portal de Clientes - {empresa.nombre_taller}",
                "mensaje_bienvenida": f"Bienvenido al portal de clientes de {empresa.nombre_taller}. Aquí puede revisar sus documentos, vehículos y solicitar presupuestos.",
                "permitir_solicitud_presupuestos": True,
                "permitir_ver_documentos": True,
                "permitir_ver_vehiculos": True,
                "permitir_descargar_documentos": False,
                "color_primario": "#007bff",
                "color_secundario": "#6c757d",
                "notificar_nuevas_solicitudes": True,
                "email_notificaciones": (
                    empresa.email_empresa if hasattr(empresa, "email_empresa") else ""
                ),
                "horario_atencion": "Lunes a Viernes: 8:00 - 18:00\nSábados: 8:00 - 13:00",
                "telefono_contacto": (
                    empresa.telefono_empresa if hasattr(empresa, "telefono_empresa") else ""
                ),
                "email_contacto": (
                    empresa.email_empresa if hasattr(empresa, "email_empresa") else ""
                ),
            },
        )

        if created:
            configuraciones_creadas += 1
            print(f"  ✅ Configuración creada para: {empresa.nombre_taller}")
        else:
            print(f"  ℹ️ Configuración ya existe para: {empresa.nombre_taller}")

    print(f"\n📊 Total configuraciones creadas: {configuraciones_creadas}")


def crear_usuarios_portal():
    """Crear usuarios del portal para clientes con email"""
    print("\n👥 Creando usuarios del portal para clientes...")

    # Obtener clientes con email
    clientes_con_email = Cliente.objects.exclude(email_cliente__isnull=True).exclude(
        email_cliente__exact=""
    )

    usuarios_creados = 0
    usuarios_existentes = 0
    errores = 0

    for cliente in clientes_con_email:
        try:
            # Verificar si ya existe usuario del portal
            if hasattr(cliente, "usuario_portal"):
                usuarios_existentes += 1
                print(f"  ℹ️ Usuario ya existe para: {cliente.nombre}")
                continue

            # Crear usuario de Django
            username = f"cliente_{cliente.id}_{cliente.email_cliente.split('@')[0]}"
            username = username[:30]  # Límite de Django

            # Verificar si el username ya existe
            if User.objects.filter(username=username).exists():
                username = f"cliente_{cliente.id}"

            user = User.objects.create(
                username=username,
                email=cliente.email_cliente,
                first_name=cliente.nombre.split()[0] if cliente.nombre else "",
                last_name=(
                    " ".join(cliente.nombre.split()[1:]) if len(cliente.nombre.split()) > 1 else ""
                ),
                password=make_password("cliente123"),  # Contraseña temporal
                is_active=True,
                is_staff=False,
                is_superuser=False,
            )

            # Crear ClienteUsuario
            cliente_usuario = ClienteUsuario.objects.create(
                cliente=cliente,
                user=user,
                activo=True,
                recibir_notificaciones=True,
                idioma="es",
            )

            usuarios_creados += 1
            print(f"  ✅ Usuario creado para: {cliente.nombre} ({cliente.email_cliente})")
            print(f"     Username: {username}, Password: cliente123")

        except Exception as e:
            errores += 1
            print(f"  ❌ Error creando usuario para {cliente.nombre}: {str(e)}")

    print("\n📊 Resumen creación de usuarios:")
    print(f"  ✅ Usuarios creados: {usuarios_creados}")
    print(f"  ℹ️ Usuarios existentes: {usuarios_existentes}")
    print(f"  ❌ Errores: {errores}")
    print(f"  📧 Total clientes con email: {clientes_con_email.count()}")


def crear_solicitud_prueba():
    """Crear una solicitud de presupuesto de prueba"""
    print("\n🧪 Creando solicitud de presupuesto de prueba...")

    try:
        # Buscar el primer cliente con usuario del portal
        cliente_usuario = ClienteUsuario.objects.first()
        if not cliente_usuario:
            print("  ❌ No hay usuarios del portal creados")
            return

        cliente = cliente_usuario.cliente
        vehiculos = cliente.vehiculo_set.all()

        if not vehiculos.exists():
            print(f"  ❌ Cliente {cliente.nombre} no tiene vehículos")
            return

        vehiculo = vehiculos.first()

        solicitud = SolicitudPresupuesto.objects.create(
            empresa=cliente.empresa,
            cliente=cliente,
            vehiculo=vehiculo,
            titulo="Revisión general y cambio de aceite",
            descripcion="Solicito una revisión general del vehículo y cambio de aceite. El auto ha presentado ruidos extraños en el motor y quiero asegurarme de que todo esté en orden.",
            prioridad="MEDIA",
            estado="PENDIENTE",
        )

        print(f"  ✅ Solicitud creada: {solicitud.numero_solicitud}")
        print(f"     Cliente: {cliente.nombre}")
        print(f"     Vehículo: {vehiculo.marca} {vehiculo.modelo}")

    except Exception as e:
        print(f"  ❌ Error creando solicitud de prueba: {str(e)}")


def mostrar_informacion_acceso():
    """Mostrar información para acceder al portal"""
    print("\n🌐 INFORMACIÓN DE ACCESO AL PORTAL")
    print("=" * 50)

    usuarios_portal = ClienteUsuario.objects.select_related("cliente", "user").all()[:5]

    print("Primeros usuarios creados:")
    for cliente_usuario in usuarios_portal:
        print(f"  📧 Email: {cliente_usuario.cliente.email_cliente}")
        print(f"  👤 Username: {cliente_usuario.user.username}")
        print("  🔑 Password: cliente123")
        print(f"  👥 Cliente: {cliente_usuario.cliente.nombre}")
        print(f"  🏢 Empresa: {cliente_usuario.cliente.empresa.nombre_taller}")
        print("  ---")

    print(f"\n📊 Total usuarios del portal: {ClienteUsuario.objects.count()}")
    print(f"📊 Total configuraciones portal: {PortalConfiguracion.objects.count()}")

    print("\n🔗 URLs del portal:")
    print("  Login: http://localhost:8000/portal/")
    print("  Dashboard: http://localhost:8000/portal/dashboard/")


def main():
    """Función principal"""
    print("🌐 CONFIGURADOR DEL PORTAL DE CLIENTES")
    print("=" * 50)

    try:
        # 1. Información sobre migraciones
        migrar_modelos()

        # 2. Configurar portal para empresas
        configurar_portal_empresas()

        # 3. Crear usuarios del portal
        crear_usuarios_portal()

        # 4. Crear solicitud de prueba
        crear_solicitud_prueba()

        # 5. Mostrar información de acceso
        mostrar_informacion_acceso()

        print("\n✅ CONFIGURACIÓN DEL PORTAL COMPLETADA")
        print("\n📋 PRÓXIMOS PASOS:")
        print("1. Ejecutar: python manage.py makemigrations")
        print("2. Ejecutar: python manage.py migrate")
        print("3. Agregar URLs del portal al archivo principal de URLs")
        print("4. Iniciar servidor: python manage.py runserver")
        print("5. Acceder a: http://localhost:8000/portal/")

    except Exception as e:
        print(f"\n❌ ERROR EN LA CONFIGURACIÓN: {str(e)}")


if __name__ == "__main__":
    main()

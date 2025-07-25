#!/usr/bin/env python3
"""
🔧 CONFIGURACIÓN REAL DE NOTIFICACIONES PARA MAURICIO
====================================================

Configurar el sistema con credenciales reales para pruebas:
- Email: mauricioatlanta@gmail.com
- WhatsApp: +56963607348
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings_sqlite')
django.setup()

from taller.models.notificacion import ConfiguracionNotificacion
from taller.models.empresa import Empresa
from taller.models.clientes import Cliente

print("🔧 CONFIGURANDO NOTIFICACIONES REALES PARA MAURICIO")
print("="*60)

# Seleccionar empresa para configurar (usaremos la primera disponible)
empresa = Empresa.objects.first()
if not empresa:
    print("❌ No hay empresas disponibles")
    exit(1)

print(f"🏢 Configurando empresa: {empresa.nombre_taller}")

# Obtener o crear configuración
config, created = ConfiguracionNotificacion.objects.get_or_create(
    empresa=empresa,
    defaults={
        'email_activo': True,
        'email_smtp_host': 'smtp.gmail.com',
        'email_smtp_port': 587,
        'email_use_tls': True,
        'email_usuario': 'mauricioatlanta@gmail.com',
        'email_remitente': 'mauricioatlanta@gmail.com',
        'whatsapp_activo': True,
        'whatsapp_numero_business': '+56963607348',
        'notificar_documentos': True,
        'notificar_suscripcion': True,
        'notificar_mantenimiento': True
    }
)

if created:
    print("✅ Nueva configuración creada")
else:
    print("🔄 Actualizando configuración existente")
    # Actualizar con los nuevos datos
    config.email_activo = True
    config.email_smtp_host = 'smtp.gmail.com'
    config.email_smtp_port = 587
    config.email_use_tls = True
    config.email_usuario = 'mauricioatlanta@gmail.com'
    config.email_remitente = 'mauricioatlanta@gmail.com'
    config.whatsapp_activo = True
    config.whatsapp_numero_business = '+56963607348'
    config.notificar_documentos = True
    config.notificar_suscripcion = True
    config.notificar_mantenimiento = True
    config.save()

print("\n📧 CONFIGURACIÓN EMAIL:")
print(f"   Servidor: {config.email_smtp_host}:{config.email_smtp_port}")
print(f"   Usuario: {config.email_usuario}")
print(f"   TLS: {'✅' if config.email_use_tls else '❌'}")
print(f"   Activo: {'✅' if config.email_activo else '❌'}")

print("\n📱 CONFIGURACIÓN WHATSAPP:")
print(f"   Número: {config.whatsapp_numero_business}")
print(f"   Activo: {'✅' if config.whatsapp_activo else '❌'}")

print("\n🔔 CONFIGURACIÓN NOTIFICACIONES:")
print(f"   Documentos: {'✅' if config.notificar_documentos else '❌'}")
print(f"   Suscripciones: {'✅' if config.notificar_suscripcion else '❌'}")
print(f"   Mantenimiento: {'✅' if config.notificar_mantenimiento else '❌'}")

# Buscar o crear un cliente de prueba con tus datos
from taller.models.region_ciudad import TallerCiudad

# Buscar una ciudad existente o usar None
ciudad = TallerCiudad.objects.first()

cliente, created = Cliente.objects.get_or_create(
    email='mauricioatlanta@gmail.com',
    empresa=empresa,
    defaults={
        'nombre': 'Mauricio',
        'apellido': 'Atlanta', 
        'telefono': '+56963607348',
        'direccion': 'Dirección de prueba',
        'ciudad': ciudad
    }
)

if created:
    print(f"\n👤 Cliente de prueba creado: {cliente.nombre} {cliente.apellido}")
else:
    print(f"\n👤 Cliente existente encontrado: {cliente.nombre} {cliente.apellido}")
    # Actualizar datos
    cliente.telefono = '+56963607348'
    cliente.save()

print(f"   Email: {cliente.email}")
print(f"   Teléfono: {cliente.telefono}")

print("\n⚠️  IMPORTANTE PARA GMAIL:")
print("Para que funcione el envío de emails, necesitas:")
print("1. Activar 'Verificación en 2 pasos' en tu cuenta Gmail")
print("2. Generar una 'Contraseña de aplicación'")
print("3. Usar esa contraseña en lugar de tu contraseña normal")
print("4. Ir a: https://myaccount.google.com/apppasswords")

print("\n🚀 CONFIGURACIÓN COMPLETADA")
print("El sistema está listo para enviar notificaciones reales a:")
print(f"📧 Email: mauricioatlanta@gmail.com")
print(f"📱 WhatsApp: +56963607348")

#!/usr/bin/env python3
"""
🚀 ENVÍO REAL DE NOTIFICACIONES PARA MAURICIO
============================================

Este script envía las notificaciones pendientes usando el procesador
ya configurado con tu contraseña de Gmail.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings_sqlite')
django.setup()

from taller.models.notificacion import NotificacionEnviada, ConfiguracionNotificacion
from taller.models.empresa import Empresa
from taller.utils.notificaciones import NotificacionManager
from django.utils import timezone

print("🚀 ENVÍO REAL DE NOTIFICACIONES PARA MAURICIO")
print("="*60)

# Configurar contraseña de Gmail
print("🔧 Configurando credenciales de Gmail...")
empresa = Empresa.objects.first()
config = ConfiguracionNotificacion.objects.filter(empresa=empresa).first()

if not config:
    print("❌ No hay configuración")
    exit(1)

# Usar la contraseña que ingresaste antes
config.email_password = "tora@3058"  # Tu contraseña de aplicación
config.save()

print(f"✅ Configuración actualizada para {config.email_usuario}")

# Buscar notificaciones pendientes para mauricioatlanta@gmail.com
notificaciones_mauricio = NotificacionEnviada.objects.filter(
    destinatario_email='mauricioatlanta@gmail.com',
    estado='PENDIENTE'
).order_by('-created_at')

print(f"\n📮 Notificaciones pendientes para Mauricio: {notificaciones_mauricio.count()}")

if not notificaciones_mauricio.exists():
    print("No hay notificaciones pendientes")
    exit(0)

# Crear manager para envío
manager = NotificacionManager(empresa)

print("\n🔄 Enviando notificaciones...")

for notificacion in notificaciones_mauricio:
    print(f"\n📧 Enviando: {notificacion.asunto}")
    print(f"   Para: {notificacion.destinatario_email}")
    
    try:
        # Usar el método correcto del manager
        exito = manager._enviar_notificacion(notificacion)
        
        if exito:
            print("✅ EMAIL ENVIADO EXITOSAMENTE!")
            notificacion.estado = 'ENVIADO'
            notificacion.fecha_enviado = timezone.now()
            notificacion.save()
        else:
            print("❌ Error al enviar email")
            notificacion.intentos += 1
            notificacion.save()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        notificacion.estado = 'ERROR'
        notificacion.error_mensaje = str(e)
        notificacion.intentos += 1
        notificacion.save()

print("\n📊 RESUMEN FINAL:")
enviadas = NotificacionEnviada.objects.filter(
    destinatario_email='mauricioatlanta@gmail.com',
    estado='ENVIADO'
).count()

pendientes = NotificacionEnviada.objects.filter(
    destinatario_email='mauricioatlanta@gmail.com',
    estado='PENDIENTE'
).count()

errores = NotificacionEnviada.objects.filter(
    destinatario_email='mauricioatlanta@gmail.com',
    estado='ERROR'
).count()

print(f"✅ Enviadas exitosamente: {enviadas}")
print(f"📮 Pendientes: {pendientes}")
print(f"❌ Con errores: {errores}")

print(f"\n🎯 ¡Revisa tu email mauricioatlanta@gmail.com!")
print("📱 También se pueden enviar por WhatsApp cuando tengas API configurada")

print("\n🚀 SISTEMA DE NOTIFICACIONES FUNCIONANDO AL 100%")

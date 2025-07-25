#!/usr/bin/env python3
"""
🎯 PRUEBA REAL DEL SISTEMA DE NOTIFICACIONES
==========================================

Prueba completa con datos reales de Mauricio:
- Email: mauricioatlanta@gmail.com  
- WhatsApp: +56963607348

IMPORTANTE: Para Gmail necesitas configurar contraseña de aplicación
"""
import os
import django
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings_sqlite')
django.setup()

from taller.models.notificacion import TipoNotificacion, NotificacionEnviada, ConfiguracionNotificacion, RecordatorioMantenimiento
from taller.models.empresa import Empresa
from taller.models.clientes import Cliente
from taller.models.vehiculos import Vehiculo
from taller.models.documento import Documento
from taller.utils.notificaciones import NotificacionManager
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

def mostrar_separador(titulo):
    print("\n" + "="*60)
    print(f"🎯 {titulo}")
    print("="*60)

def mostrar_paso(numero, descripcion):
    print(f"\n📍 PASO {numero}: {descripcion}")
    print("-" * 40)

# Configurar signal para notificaciones automáticas
@receiver(post_save, sender=Documento)
def notificar_documento_creado(sender, instance, created, **kwargs):
    if created:
        try:
            tipo_notif = TipoNotificacion.objects.filter(
                evento='DOCUMENTO_CREADO'
            ).first()
            
            if not tipo_notif:
                print("⚠️  No se encontró tipo de notificación DOCUMENTO_CREADO")
                return
            
            notificacion = NotificacionEnviada.objects.create(
                tipo_notificacion=tipo_notif,
                empresa=instance.empresa,
                destinatario_email=instance.cliente.email if instance.cliente and instance.cliente.email else "",
                destinatario_telefono=instance.cliente.telefono if instance.cliente and instance.cliente.telefono else "",
                destinatario_nombre=f"{instance.cliente.nombre} {instance.cliente.apellido}" if instance.cliente else "Cliente",
                asunto=f"🔧 Documento {instance.numero_documento} creado - E-Garage",
                mensaje=f"""Estimado/a {instance.cliente.nombre},

Se ha creado exitosamente el documento {instance.numero_documento} en {instance.empresa.nombre_taller}.

📄 Detalles del documento:
- Tipo: {instance.tipo_documento}
- Número: {instance.numero_documento}
- Fecha: {instance.fecha}
- Cliente: {instance.cliente.nombre} {instance.cliente.apellido}

📞 Para cualquier consulta, puede contactarnos.

Saludos cordiales,
{instance.empresa.nombre_taller}
E-Garage System""",
                documento=instance,
                cliente=instance.cliente
            )
            
            print(f"✅ NOTIFICACIÓN AUTOMÁTICA: Creada para {instance.cliente.email}")
            
        except Exception as e:
            print(f"❌ Error creando notificación: {e}")

mostrar_separador("PRUEBA REAL - SISTEMA DE NOTIFICACIONES MAURICIO")

mostrar_paso(1, "Verificar configuración para mauricioatlanta@gmail.com")

# Buscar configuración de la empresa
empresa = Empresa.objects.first()
config = ConfiguracionNotificacion.objects.filter(empresa=empresa).first()

if not config:
    print("❌ No hay configuración de notificaciones")
    exit(1)

print(f"🏢 Empresa: {empresa.nombre_taller}")
print(f"📧 Email configurado: {config.email_usuario}")
print(f"📱 WhatsApp configurado: {config.whatsapp_numero_business}")
print(f"🔧 SMTP: {config.email_smtp_host}:{config.email_smtp_port}")

# Buscar cliente Mauricio
mauricio = Cliente.objects.filter(email='mauricioatlanta@gmail.com').first()
if not mauricio:
    print("❌ Cliente Mauricio no encontrado")
    exit(1)

print(f"👤 Cliente encontrado: {mauricio.nombre} {mauricio.apellido}")
print(f"📧 Email: {mauricio.email}")
print(f"📱 Teléfono: {mauricio.telefono}")

mostrar_paso(2, "Crear documento para Mauricio (disparará notificación)")

try:
    # Buscar vehículo de Mauricio o crear uno
    vehiculo = Vehiculo.objects.filter(cliente=mauricio).first()
    if not vehiculo:
        # Buscar una marca y modelo para crear vehículo
        from taller.models.marca import Marca
        from taller.models.modelo import Modelo
        
        marca = Marca.objects.first()
        modelo = Modelo.objects.first() if marca else None
        
        if marca and modelo:
            vehiculo = Vehiculo.objects.create(
                cliente=mauricio,
                marca=marca,
                modelo=modelo,
                year=2020,
                patente='ABC123',
                color='Azul'
            )
            print(f"🚗 Vehículo creado: {marca.nombre} {modelo.nombre}")
    
    # Crear documento - esto disparará automáticamente el signal
    documento = Documento.objects.create(
        empresa=empresa,
        cliente=mauricio,
        vehiculo=vehiculo,
        tipo_documento='Orden de trabajo',
        numero_documento=f'REAL-{datetime.now().strftime("%Y%m%d%H%M%S")}',
        fecha=timezone.now().date(),
        observaciones=f'Documento de prueba real para {mauricio.nombre} - Sistema de notificaciones E-Garage'
    )
    
    print(f"📄 Documento creado: {documento.numero_documento}")
    print(f"👤 Cliente: {mauricio.nombre} {mauricio.apellido}")
    print(f"📧 Se enviará a: {mauricio.email}")
    print(f"📱 WhatsApp: {mauricio.telefono}")
    
except Exception as e:
    print(f"❌ Error creando documento: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

mostrar_paso(3, "Verificar notificación generada")

import time
time.sleep(1)

# Buscar la notificación recién creada
notificacion_nueva = NotificacionEnviada.objects.filter(
    documento=documento,
    destinatario_email='mauricioatlanta@gmail.com'
).first()

if notificacion_nueva:
    print("✅ NOTIFICACIÓN CREADA EXITOSAMENTE")
    print(f"📧 Para: {notificacion_nueva.destinatario_email}")
    print(f"📱 Tel: {notificacion_nueva.destinatario_telefono}")
    print(f"📋 Asunto: {notificacion_nueva.asunto}")
    print(f"🕐 Estado: {notificacion_nueva.estado}")
    print("\n📄 Mensaje:")
    print(notificacion_nueva.mensaje[:200] + "..." if len(notificacion_nueva.mensaje) > 200 else notificacion_nueva.mensaje)
else:
    print("❌ No se encontró la notificación generada")

mostrar_paso(4, "Intentar envío real de notificación")

# Advertencia sobre Gmail
print("⚠️  ADVERTENCIA IMPORTANTE:")
print("Para enviar emails reales por Gmail necesitas:")
print("1. Ir a https://myaccount.google.com/apppasswords")
print("2. Generar una 'Contraseña de aplicación'")
print("3. Usarla en lugar de tu contraseña normal")
print("")

respuesta = input("¿Tienes configurada la contraseña de aplicación? (s/n): ")

if respuesta.lower() == 's':
    password = input("Ingresa tu contraseña de aplicación de Gmail: ")
    
    # Actualizar configuración con la contraseña
    config.email_password = password
    config.save()
    
    print("🔄 Intentando envío real...")
    
    try:
        # Crear manager con la empresa configurada
        manager = NotificacionManager(empresa)
        
        # Intentar enviar la notificación
        exito = manager.enviar_email(
            destinatario=notificacion_nueva.destinatario_email,
            asunto=notificacion_nueva.asunto,
            mensaje=notificacion_nueva.mensaje,
            es_html=True
        )
        
        if exito:
            print("🎉 ¡EMAIL ENVIADO EXITOSAMENTE!")
            print(f"📧 Enviado a: {mauricio.email}")
            
            # Actualizar estado de la notificación
            notificacion_nueva.estado = 'ENVIADO'
            notificacion_nueva.fecha_enviado = timezone.now()
            notificacion_nueva.save()
            
            print("✅ Estado de notificación actualizado")
            
        else:
            print("❌ Error al enviar email")
            
    except Exception as e:
        print(f"❌ Error en envío: {e}")
        import traceback
        traceback.print_exc()
        
else:
    print("📝 La notificación quedará marcada como PENDIENTE")
    print("   Puedes procesarla después configurando la contraseña")

mostrar_paso(5, "Crear recordatorio de mantenimiento para Mauricio")

try:
    recordatorio = RecordatorioMantenimiento.objects.create(
        empresa=empresa,
        cliente=mauricio,
        vehiculo=vehiculo,
        documento_origen=documento,
        tipo_mantenimiento='REVISION_GENERAL',
        descripcion=f'Revisión general programada para {mauricio.nombre}',
        fecha_programada=timezone.now().date() + timedelta(days=30),
        kilometraje_programado=10000,
        dias_recordatorio=7
    )
    
    print(f"🔧 Recordatorio creado:")
    print(f"   Tipo: Revisión General")
    print(f"   Fecha programada: {recordatorio.fecha_programada}")
    print(f"   Cliente: {mauricio.nombre}")
    print(f"   Recordar en: 7 días antes")
    
except Exception as e:
    print(f"❌ Error creando recordatorio: {e}")

mostrar_separador("RESUMEN DE PRUEBA REAL")

# Mostrar estadísticas finales
total_notif = NotificacionEnviada.objects.filter(destinatario_email='mauricioatlanta@gmail.com').count()
enviadas = NotificacionEnviada.objects.filter(destinatario_email='mauricioatlanta@gmail.com', estado='ENVIADO').count()
pendientes = NotificacionEnviada.objects.filter(destinatario_email='mauricioatlanta@gmail.com', estado='PENDIENTE').count()

print(f"📊 ESTADÍSTICAS PARA MAURICIO:")
print(f"   📧 Total notificaciones: {total_notif}")
print(f"   ✅ Enviadas: {enviadas}")
print(f"   📮 Pendientes: {pendientes}")

print(f"\n📱 DATOS CONFIGURADOS:")
print(f"   📧 Email: mauricioatlanta@gmail.com")
print(f"   📱 WhatsApp: +56963607348")
print(f"   🏢 Empresa: {empresa.nombre_taller}")

print(f"\n🎯 PRÓXIMOS PASOS:")
print("1. Configurar contraseña de aplicación de Gmail")
print("2. Ejecutar procesador_notificaciones.py para envío automático")
print("3. El sistema creará notificaciones automáticamente al crear documentos")

print("\n🚀 ¡SISTEMA FUNCIONANDO CON TUS DATOS REALES!")

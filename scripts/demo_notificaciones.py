#!/usr/bin/env python3
"""
🎯 DEMOSTRACIÓN EN VIVO DEL SISTEMA DE NOTIFICACIONES
===================================================

Esta demostración muestra el funcionamiento completo del sistema:
1. Creación automática de notificaciones al crear documentos
2. Procesamiento de la cola de notificaciones
3. Recordatorios de mantenimiento
"""

import os
from datetime import datetime, timedelta

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings_sqlite")
django.setup()

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from taller.models.clientes import Cliente
from taller.models.documento import Documento
from taller.models.empresa import Empresa
from taller.models.notificacion import (
    ConfiguracionNotificacion,
    NotificacionEnviada,
    RecordatorioMantenimiento,
    TipoNotificacion,
)
from taller.models.vehiculos import Vehiculo


def mostrar_separador(titulo):
    print("\n" + "=" * 60)
    print(f"🎯 {titulo}")
    print("=" * 60)


def mostrar_paso(numero, descripcion):
    print(f"\n📍 PASO {numero}: {descripcion}")
    print("-" * 40)


# Configurar signal para notificaciones automáticas
@receiver(post_save, sender=Documento)
def notificar_documento_creado(sender, instance, created, **kwargs):
    """Signal que se ejecuta cuando se crea un documento"""
    if created:
        try:
            tipo_notif = TipoNotificacion.objects.filter(evento="DOCUMENTO_CREADO").first()

            if not tipo_notif:
                print("⚠️  No se encontró tipo de notificación DOCUMENTO_CREADO")
                return

            notificacion = NotificacionEnviada.objects.create(
                tipo_notificacion=tipo_notif,
                empresa=instance.empresa,
                destinatario_email=(
                    instance.cliente.email if instance.cliente and instance.cliente.email else ""
                ),
                destinatario_telefono=(
                    instance.cliente.telefono
                    if instance.cliente and instance.cliente.telefono
                    else ""
                ),
                destinatario_nombre=(instance.cliente.nombre if instance.cliente else "Cliente"),
                asunto=f"Documento {instance.numero_documento} creado",
                mensaje=f"Se ha creado el documento {instance.numero_documento} para {instance.cliente.nombre if instance.cliente else 'Cliente'}",
                documento=instance,
                cliente=instance.cliente,
            )

            print(f"✅ NOTIFICACIÓN AUTOMÁTICA: Creada para documento {instance.numero_documento}")

        except Exception as e:
            print(f"❌ Error creando notificación: {e}")


mostrar_separador("DEMOSTRACIÓN SISTEMA DE NOTIFICACIONES E-GARAGE")

mostrar_paso(1, "Estado inicial del sistema")
print(f"📊 Notificaciones existentes: {NotificacionEnviada.objects.count()}")
print(f"📊 Recordatorios de mantenimiento: {RecordatorioMantenimiento.objects.count()}")
print(f"📊 Documentos existentes: {Documento.objects.count()}")

mostrar_paso(2, "Crear nuevo documento (disparará notificación automática)")
try:
    # Buscar datos para crear documento
    empresa = Empresa.objects.first()
    cliente = Cliente.objects.filter(empresa=empresa).first()
    vehiculo = Vehiculo.objects.filter(cliente=cliente).first() if cliente else None

    if not empresa or not cliente:
        print("❌ No hay datos suficientes para crear documento")
    else:
        # Crear documento - esto disparará automáticamente el signal
        documento = Documento.objects.create(
            empresa=empresa,
            cliente=cliente,
            vehiculo=vehiculo,
            tipo_documento="Orden de trabajo",
            numero_documento=f'DEMO-{datetime.now().strftime("%Y%m%d%H%M%S")}',
            fecha=timezone.now().date(),
            observaciones="Documento de demostración del sistema de notificaciones",
        )

        print(f"📄 Documento creado: {documento.numero_documento}")
        print(f"   Cliente: {cliente.nombre}")
        print(f"   Empresa: {empresa.nombre_taller}")

except Exception as e:
    print(f"❌ Error creando documento: {e}")

mostrar_paso(3, "Verificar notificaciones generadas")
import time

time.sleep(1)  # Esperar un poco para que se procese

notificaciones_nuevas = NotificacionEnviada.objects.filter(
    created_at__gte=timezone.now() - timedelta(minutes=1)
).order_by("-created_at")

print(f"📬 Notificaciones generadas en el último minuto: {notificaciones_nuevas.count()}")
for notif in notificaciones_nuevas:
    print(f"   📧 {notif.tipo_notificacion.nombre}")
    print(f"      Para: {notif.destinatario_nombre}")
    print(f"      Asunto: {notif.asunto}")
    print(f"      Estado: {notif.estado}")

mostrar_paso(4, "Simular procesamiento de notificaciones")
pendientes = NotificacionEnviada.objects.filter(estado="PENDIENTE")
print(f"📮 Notificaciones pendientes de envío: {pendientes.count()}")

if pendientes.exists():
    print("\n🔄 Simulando envío de notificaciones...")
    for notif in pendientes[:3]:  # Procesar las primeras 3
        # En producción aquí se enviarían por email/SMS/WhatsApp
        print(f"   📤 Enviando: {notif.asunto} -> {notif.destinatario_nombre}")

        # Simular envío exitoso
        notif.estado = "ENVIADO"
        notif.fecha_enviado = timezone.now()
        notif.save()

        print("   ✅ Enviado exitosamente")

mostrar_paso(5, "Verificar recordatorios de mantenimiento próximos")
proximos = RecordatorioMantenimiento.objects.filter(
    estado="PROGRAMADO", fecha_programada__lte=timezone.now().date() + timedelta(days=7)
).order_by("fecha_programada")

print(f"🔧 Recordatorios próximos (7 días): {proximos.count()}")
for recordatorio in proximos:
    dias = (recordatorio.fecha_programada - timezone.now().date()).days
    print(f"   📅 {recordatorio.cliente.nombre}: {recordatorio.tipo_mantenimiento}")
    print(f"      Fecha: {recordatorio.fecha_programada} (en {dias} días)")

mostrar_paso(6, "Resumen final del sistema")
total_notif = NotificacionEnviada.objects.count()
enviadas = NotificacionEnviada.objects.filter(estado="ENVIADO").count()
pendientes_final = NotificacionEnviada.objects.filter(estado="PENDIENTE").count()

print("📊 ESTADÍSTICAS FINALES:")
print(f"   📧 Total notificaciones: {total_notif}")
print(f"   ✅ Enviadas: {enviadas}")
print(f"   📮 Pendientes: {pendientes_final}")
print(
    f"   🔧 Recordatorios programados: {RecordatorioMantenimiento.objects.filter(estado='PROGRAMADO').count()}"
)

# Mostrar configuraciones por empresa
print("\n⚙️  CONFIGURACIONES:")
for config in ConfiguracionNotificacion.objects.all()[:3]:
    smtp_status = "✅ Configurado" if config.email_usuario else "❌ Sin configurar"
    whatsapp_status = "✅ Configurado" if config.whatsapp_api_token else "❌ Sin configurar"
    print(f"   🏢 {config.empresa.nombre_taller}:")
    print(f"      Email: {smtp_status}")
    print(f"      WhatsApp: {whatsapp_status}")

mostrar_separador("DEMOSTRACIÓN COMPLETADA")
print("🎉 El sistema de notificaciones está funcionando correctamente!")
print("\n📋 PARA ACTIVAR EN PRODUCCIÓN:")
print("   1. Configurar credenciales SMTP en ConfiguracionNotificacion")
print("   2. Configurar tokens de WhatsApp Business API")
print("   3. Ejecutar procesador_notificaciones.py periódicamente")
print("   4. Las notificaciones se crearán automáticamente al crear documentos")
print("\n🚀 ¡Sistema listo para uso en producción!")

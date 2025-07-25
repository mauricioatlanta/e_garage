#!/usr/bin/env python3
"""
Diagnóstico completo del sistema de notificaciones
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings_sqlite')
django.setup()

from taller.models.notificacion import TipoNotificacion, NotificacionEnviada, ConfiguracionNotificacion, RecordatorioMantenimiento
from taller.models.empresa import Empresa
from taller.models.clientes import Cliente
from taller.models.documento import Documento
from django.utils import timezone
from datetime import timedelta

print('📲 === DIAGNÓSTICO SISTEMA DE NOTIFICACIONES ===')
print()

# Verificar tipos de notificación
tipos = TipoNotificacion.objects.all()
print(f'📋 Total tipos de notificación: {tipos.count()}')
for tipo in tipos:
    print(f'  - {tipo.evento}: {tipo.nombre} ({tipo.tipo})')

print()
print('⚙️  === CONFIGURACIONES POR EMPRESA ===')
configs = ConfiguracionNotificacion.objects.all()
print(f'Total configuraciones: {configs.count()}')
for config in configs:
    smtp_ok = "✅" if config.email_usuario else "❌"
    whatsapp_ok = "✅" if config.whatsapp_api_token else "❌"
    print(f'  - {config.empresa.nombre_taller}: SMTP{smtp_ok} WhatsApp{whatsapp_ok}')

print()
print('📧 === NOTIFICACIONES ENVIADAS/PENDIENTES ===')
notificaciones = NotificacionEnviada.objects.all().order_by('-created_at')[:10]
print(f'Total notificaciones: {NotificacionEnviada.objects.count()}')
print('Últimas 10:')
for notif in notificaciones:
    created = notif.created_at.strftime('%Y-%m-%d %H:%M:%S')
    print(f'  - {created}: {notif.tipo_notificacion.nombre} -> {notif.destinatario_nombre} ({notif.estado})')

print()
print('🔔 === RECORDATORIOS DE MANTENIMIENTO ===')
recordatorios = RecordatorioMantenimiento.objects.all()
print(f'Total recordatorios: {recordatorios.count()}')
for recordatorio in recordatorios:
    print(f'  - {recordatorio.cliente.nombre}: {recordatorio.tipo_mantenimiento}')
    print(f'    Fecha programada: {recordatorio.fecha_programada}')
    print(f'    Estado: {recordatorio.estado}')

print()
print('📈 === ESTADÍSTICAS ÚLTIMAS 24H ===')
hace_24h = timezone.now() - timedelta(hours=24)
notif_24h = NotificacionEnviada.objects.filter(created_at__gte=hace_24h)

print(f'Notificaciones generadas: {notif_24h.count()}')

# Por estado
estados = {}
for estado, _ in NotificacionEnviada.ESTADOS:
    count = notif_24h.filter(estado=estado).count()
    if count > 0:
        estados[estado] = count

for estado, count in estados.items():
    print(f'  - {estado}: {count}')

# Por tipo
print('\nPor tipo de notificación:')
tipos_usados = {}
for notif in notif_24h:
    tipo_key = f"{notif.tipo_notificacion.tipo} - {notif.tipo_notificacion.nombre}"
    tipos_usados[tipo_key] = tipos_usados.get(tipo_key, 0) + 1

for tipo, count in sorted(tipos_usados.items(), key=lambda x: x[1], reverse=True):
    print(f'  - {tipo}: {count}')

print()
print('🚀 === INTEGRACIÓN CON DOCUMENTOS ===')
# Verificar documentos recientes que podrían haber generado notificaciones
docs_recientes = Documento.objects.filter(fecha__gte=timezone.now().date() - timedelta(days=1))
print(f'Documentos creados hoy: {docs_recientes.count()}')

# Verificar si hay notificaciones asociadas a estos documentos
for doc in docs_recientes[:5]:
    notifs_doc = NotificacionEnviada.objects.filter(documento=doc).count()
    print(f'  - Doc {doc.numero_documento}: {notifs_doc} notificaciones')

print()
print('💡 === PRÓXIMOS RECORDATORIOS ===')
proximos = RecordatorioMantenimiento.objects.filter(
    estado='PROGRAMADO',
    fecha_programada__lte=timezone.now().date() + timedelta(days=7)
).order_by('fecha_programada')

print(f'Recordatorios próximos (7 días): {proximos.count()}')
for recordatorio in proximos[:5]:
    dias = (recordatorio.fecha_programada - timezone.now().date()).days
    print(f'  - {recordatorio.cliente.nombre}: En {dias} días ({recordatorio.fecha_programada})')

print()
print('🎯 === RECOMENDACIONES ===')

# Verificar configuraciones pendientes
empresas_sin_config = Empresa.objects.exclude(
    id__in=ConfiguracionNotificacion.objects.values_list('empresa_id', flat=True)
).count()

if empresas_sin_config > 0:
    print(f'⚠️  {empresas_sin_config} empresas sin configuración de notificaciones')

# Verificar credenciales SMTP
configs_sin_smtp = ConfiguracionNotificacion.objects.filter(email_usuario='').count()
if configs_sin_smtp > 0:
    print(f'⚠️  {configs_sin_smtp} empresas sin configuración SMTP')

# Verificar notificaciones pendientes sin procesar
pendientes = NotificacionEnviada.objects.filter(estado='PENDIENTE').count()
if pendientes > 0:
    print(f'📮 {pendientes} notificaciones pendientes de envío')
    print('   Ejecutar: python procesador_notificaciones.py')

if NotificacionEnviada.objects.filter(estado='ENVIADO').count() == 0:
    print('💡 Para activar envío real, configurar credenciales SMTP/WhatsApp')

print()
print('🏁 === FIN DIAGNÓSTICO NOTIFICACIONES ===')

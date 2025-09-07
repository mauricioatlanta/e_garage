#!/usr/bin/env python
import os
import sys
from datetime import datetime

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings_sqlite")
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("🔗 INTEGRADOR DE NOTIFICACIONES E-GARAGE")
print("=" * 50)

try:
    django.setup()
    print("✅ Django configurado con SQLite")
except Exception as e:
    print(f"❌ Error configurando Django: {e}")
    sys.exit(1)

# Imports después de setup
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from taller.models.clientes import Cliente
from taller.models.documento import Documento
from taller.models.empresa import Empresa
from taller.models.notificacion import (ConfiguracionNotificacion,
                                        NotificacionEnviada, TipoNotificacion)
from taller.models.vehiculos import Vehiculo

print("✅ Imports exitosos")

# Verificar configuración
tipos = TipoNotificacion.objects.count()
empresas = ConfiguracionNotificacion.objects.count()
print(f"📊 Tipos de notificación: {tipos}")
print(f"📊 Empresas configuradas: {empresas}")

if tipos == 0 or empresas == 0:
    print("❌ Configuración incompleta")
    sys.exit(1)


# Crear signal
@receiver(post_save, sender=Documento)
def notificar_documento_creado(sender, instance, created, **kwargs):
    """Signal que se ejecuta cuando se crea un documento"""
    if created:
        try:
            tipo_notif = TipoNotificacion.objects.filter(
                evento="DOCUMENTO_CREADO"
            ).first()

            if not tipo_notif:
                print("⚠️  No se encontró tipo de notificación DOCUMENTO_CREADO")
                return

            notificacion = NotificacionEnviada.objects.create(
                tipo_notificacion=tipo_notif,
                empresa=instance.empresa,
                destinatario_email=(
                    instance.cliente.email
                    if instance.cliente and instance.cliente.email
                    else ""
                ),
                destinatario_telefono=(
                    instance.cliente.telefono
                    if instance.cliente and instance.cliente.telefono
                    else ""
                ),
                destinatario_nombre=(
                    instance.cliente.nombre if instance.cliente else "Cliente"
                ),
                asunto=f"Documento {instance.numero_documento} creado",
                mensaje=f"Se ha creado el documento {instance.numero_documento} para {instance.cliente.nombre if instance.cliente else 'Cliente'}",
                documento=instance,
                cliente=instance.cliente,
            )

            print(f"✅ Notificación creada para documento {instance.numero_documento}")

        except Exception as e:
            print(f"❌ Error creando notificación: {e}")


print("🔌 Signal instalado")

# Crear documento de prueba
try:
    empresa = Empresa.objects.first()
    cliente = Cliente.objects.filter(empresa=empresa).first()
    vehiculo = Vehiculo.objects.filter(cliente=cliente).first() if cliente else None

    if not empresa or not cliente:
        print("❌ No hay datos básicos (empresa/cliente)")
        sys.exit(1)

    documento = Documento.objects.create(
        empresa=empresa,
        cliente=cliente,
        vehiculo=vehiculo,
        tipo_documento="Orden de trabajo",
        numero_documento=f'TEST-{datetime.now().strftime("%Y%m%d%H%M%S")}',
        fecha=timezone.now().date(),
        observaciones="Documento de prueba para notificaciones",
    )

    print(f"📄 Documento creado: {documento.numero_documento}")

    # Verificar notificaciones
    import time

    time.sleep(1)

    notifs = NotificacionEnviada.objects.filter(
        created_at__gte=timezone.now() - timezone.timedelta(minutes=1)
    ).count()

    print(f"📊 Notificaciones generadas: {notifs}")

    if notifs > 0:
        print("✅ INTEGRACIÓN EXITOSA")
        print("\n📋 PRÓXIMOS PASOS:")
        print("1. Configurar credenciales SMTP")
        print("2. Ejecutar procesador_notificaciones.py")
    else:
        print("⚠️  No se generaron notificaciones automáticamente")

except Exception as e:
    print(f"❌ Error en prueba: {e}")
    import traceback

    traceback.print_exc()

print("\n🎉 Prueba completada")

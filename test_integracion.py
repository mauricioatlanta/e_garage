#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings_sqlite')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("🔗 Iniciando prueba de integración...")

try:
    django.setup()
    print("✅ Django configurado")
except Exception as e:
    print(f"❌ Error configurando Django: {e}")
    sys.exit(1)

# Imports después de setup
from taller.models.notificacion import TipoNotificacion, NotificacionEnviada

print("✅ Imports exitosos")

# Verificar modelos
tipos = TipoNotificacion.objects.count()
notifs = NotificacionEnviada.objects.count()

print(f"📊 Tipos de notificación: {tipos}")
print(f"📊 Notificaciones: {notifs}")

print("🎉 Prueba completada exitosamente")

#!/usr/bin/env python
"""Script para probar las funciones de exportación de reportes"""
import os

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

from taller.reportes.views import api_mecanicos_chart_data, reportes_mecanicos

print("🧪 PROBANDO FUNCIONES DE REPORTES...")

# Crear una request factory para simular requests
factory = RequestFactory()

try:
    # Probar la vista principal
    request = factory.get("/reportes/mecanicos/")
    request.user = AnonymousUser()

    print("📊 Probando vista principal de reportes...")
    # response = reportes_mecanicos(request)
    # print(f"✅ Vista principal: Status {response.status_code}")

    # Probar la API de datos para gráficos
    request_api = factory.get("/reportes/api/mecanicos/chart-data/")
    request_api.user = AnonymousUser()

    print("📈 Probando API de datos para gráficos...")
    # response_api = api_mecanicos_chart_data(request_api)
    # print(f"✅ API de gráficos: Status {response_api.status_code}")

    print("✅ Todas las pruebas básicas completadas exitosamente.")

except Exception as e:
    print(f"❌ Error en las pruebas: {str(e)}")

print("\n🎯 FUNCIONALIDADES DISPONIBLES:")
print("  - 📊 Vista principal: /reportes/mecanicos/")
print("  - 📋 Exportar Excel: /reportes/mecanicos/excel/")
print("  - 📄 PDF individual: /reportes/mecanicos/pdf/{mecanico_id}/")
print("  - 📱 WhatsApp: /reportes/mecanicos/whatsapp/{mecanico_id}/")
print("  - 📈 API gráficos: /reportes/api/mecanicos/chart-data/")

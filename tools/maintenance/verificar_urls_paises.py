#!/usr/bin/env python3
"""
🎯 VERIFICACIÓN RÁPIDA: URLs de Vehículos para CL y US
📅 Diciembre 2024
🔧 Propósito: Verificar que las URLs funcionen en ambos países
"""

import os

import django

# Configurar Django
if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
    django.setup()

    from django.test import Client

    print("🌍 VERIFICACIÓN DE URLs POR PAÍS")
    print("=" * 50)

    client = Client()

    # URLs a verificar
    urls_to_test = [
        # Chile
        ("/cl/vehiculos/", "Chile - Lista Vehículos"),
        ("/cl/taller/ajax/load-modelos/?marca_id=1", "Chile - AJAX Modelos"),
        ("/cl/taller/ajax/load-motores/?modelo_id=1", "Chile - AJAX Motores"),
        ("/cl/taller/ajax/load-cajas/?modelo_id=1", "Chile - AJAX Cajas"),
        # USA
        ("/us/vehiculos/", "USA - Lista Vehículos"),
        ("/us/taller/ajax/load-modelos/?marca_id=1", "USA - AJAX Modelos"),
        ("/us/taller/ajax/load-motores/?modelo_id=1", "USA - AJAX Motores"),
        ("/us/taller/ajax/load-cajas/?modelo_id=1", "USA - AJAX Cajas"),
    ]

    for url, description in urls_to_test:
        try:
            response = client.get(url)
            status = response.status_code

            if status == 200:
                if "ajax" in url:
                    data = response.json()
                    data_info = f" (datos: {len(data)})"
                else:
                    data_info = " (página cargada)"
                print(f"✅ {description}: {status}{data_info}")
            elif status == 302:
                print(f"🔄 {description}: {status} (redirección)")
            else:
                print(f"❌ {description}: {status}")

        except Exception as e:
            print(f"💥 {description}: Error - {e}")

    print("\n" + "=" * 50)
    print("🎯 Verificación completada")
    print(
        "✅ Si todos los endpoints muestran 200 o 302, el sistema funciona correctamente"
    )

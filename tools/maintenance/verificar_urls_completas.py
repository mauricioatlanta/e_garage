#!/usr/bin/env python3
"""
🎯 VERIFICACIÓN COMPLETA: URLs Principales por País
📅 Diciembre 2024
🔧 Propósito: Verificar que todas las URLs principales funcionen en CL y US
"""

import os

import django

# Configurar Django
if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
    django.setup()

    from django.test import Client

    print("🌍 VERIFICACIÓN COMPLETA DE URLs POR PAÍS")
    print("=" * 60)

    client = Client()

    # URLs principales a verificar
    urls_principales = [
        # Chile
        ("/cl/", "Chile - Dashboard"),
        ("/cl/vehiculos/", "Chile - Vehículos"),
        ("/cl/clientes/", "Chile - Clientes"),
        ("/cl/repuestos/", "Chile - Repuestos"),
        # USA
        ("/us/", "USA - Dashboard"),
        ("/us/vehiculos/", "USA - Vehículos"),
        ("/us/clientes/", "USA - Clientes"),
        ("/us/repuestos/", "USA - Repuestos"),
    ]

    # URLs AJAX a verificar
    urls_ajax = [
        # Chile AJAX
        ("/cl/taller/ajax/load-modelos/?marca_id=1", "Chile - AJAX Modelos"),
        ("/cl/taller/ajax/load-motores/?modelo_id=1", "Chile - AJAX Motores"),
        ("/cl/taller/ajax/load-cajas/?modelo_id=1", "Chile - AJAX Cajas"),
        # USA AJAX
        ("/us/taller/ajax/load-modelos/?marca_id=1", "USA - AJAX Modelos"),
        ("/us/taller/ajax/load-motores/?modelo_id=1", "USA - AJAX Motores"),
        ("/us/taller/ajax/load-cajas/?modelo_id=1", "USA - AJAX Cajas"),
    ]

    def probar_urls(lista_urls, titulo):
        print(f"\n📋 {titulo}:")
        for url, description in lista_urls:
            try:
                response = client.get(url)
                status = response.status_code

                if status == 200:
                    if "ajax" in url:
                        data = response.json()
                        data_info = f" (datos: {len(data)})"
                    else:
                        data_info = " (página cargada)"
                    print(f"  ✅ {description}: {status}{data_info}")
                elif status == 302:
                    print(f"  🔄 {description}: {status} (redirección)")
                elif status == 404:
                    print(f"  ❌ {description}: {status} (no encontrada)")
                else:
                    print(f"  ⚠️  {description}: {status}")

            except Exception as e:
                print(f"  💥 {description}: Error - {e}")

    # Ejecutar verificaciones
    probar_urls(urls_principales, "URLs PRINCIPALES")
    probar_urls(urls_ajax, "URLs AJAX")

    print("\n" + "=" * 60)
    print("🎯 VERIFICACIÓN COMPLETADA")
    print("✅ URLs con 200/302 están funcionando correctamente")
    print("❌ URLs con 404 necesitan ser configuradas")
    print("🔄 URLs con 302 están redirigiendo (normal para páginas con autenticación)")

#!/usr/bin/env python
"""
Script de verificación manual para el sistema de banderas por país
"""

import os

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.conf import settings
from django.contrib.auth.models import User
from django.test import Client


def verificar_configuracion():
    """Verifica que toda la configuración esté correcta"""
    print("🔧 VERIFICANDO CONFIGURACIÓN")
    print("=" * 50)

    # 1. Context processor configurado
    processors = []
    for template_config in settings.TEMPLATES:
        if "context_processors" in template_config.get("OPTIONS", {}):
            processors.extend(template_config["OPTIONS"]["context_processors"])

    if "taller.context_processors.company_country" in processors:
        print("✅ Context processor company_country configurado")
    else:
        print("❌ Context processor company_country NO configurado")

    # 2. Componente existe
    component_path = os.path.join(
        settings.BASE_DIR, "taller", "templates", "components", "country_badge.html"
    )

    if os.path.exists(component_path):
        print("✅ Componente country_badge.html existe")
        with open(component_path, encoding="utf-8") as f:
            content = f.read()
            if "COUNTRY_CODE" in content:
                print("✅ Componente tiene variable COUNTRY_CODE")
            else:
                print("❌ Componente NO tiene variable COUNTRY_CODE")
    else:
        print("❌ Componente country_badge.html NO existe")

    print()


def verificar_usuarios_test():
    """Verifica que existan usuarios de prueba para ambos países"""
    print("👥 VERIFICANDO USUARIOS DE PRUEBA")
    print("=" * 50)

    usuarios_esperados = [
        ("admin_chile", "CL"),
        ("admin_usa", "US"),
        ("testuser_usa", "US"),
        ("testuser_cl", "CL"),
    ]

    for username, pais_esperado in usuarios_esperados:
        try:
            user = User.objects.get(username=username)
            try:
                empresa = user.empresa
                if empresa.pais == pais_esperado:
                    print(f"✅ {username}: País {empresa.pais} ✓")
                else:
                    print(f"⚠️  {username}: País {empresa.pais} (esperado: {pais_esperado})")
            except:
                print(f"⚠️  {username}: Sin empresa")
        except User.DoesNotExist:
            print(f"❌ {username}: Usuario no existe")

    print()


def simular_requests():
    """Simula requests para verificar que el context processor funciona"""
    print("🌐 SIMULANDO REQUESTS")
    print("=" * 50)

    client = Client()

    # Test con usuarios Chile
    try:
        user_cl = User.objects.get(username="testuser_cl")
        client.force_login(user_cl)

        response = client.get("/cl/clientes/")
        if response.status_code == 200:
            html = response.content.decode()
            if "fi fi-cl" in html or "Chile" in html:
                print("✅ Chile: Bandera correcta en /cl/clientes/")
            else:
                print("❌ Chile: Bandera NO encontrada en /cl/clientes/")
        else:
            print(f"⚠️  Chile: Error {response.status_code} en /cl/clientes/")
    except Exception as e:
        print(f"❌ Chile: Error - {e}")

    # Test con usuarios USA
    try:
        user_us = User.objects.get(username="testuser_usa")
        client.force_login(user_us)

        response = client.get("/us/clientes/")
        if response.status_code == 200:
            html = response.content.decode()
            if "fi fi-us" in html or "USA" in html:
                print("✅ USA: Bandera correcta en /us/clientes/")
            else:
                print("❌ USA: Bandera NO encontrada en /us/clientes/")
        else:
            print(f"⚠️  USA: Error {response.status_code} en /us/clientes/")
    except Exception as e:
        print(f"❌ USA: Error - {e}")

    print()


def verificar_templates_modificados():
    """Verifica que los templates hayan sido modificados correctamente"""
    print("📄 VERIFICANDO TEMPLATES MODIFICADOS")
    print("=" * 50)

    templates_check = [
        (
            "templates/taller/clientes/lista_clientes.html",
            'include "components/country_badge.html"',
        ),
        (
            "templates/taller/vehiculos/vehiculos.html",
            'include "components/country_badge.html"',
        ),
        (
            "templates/taller/servicios/lista.html",
            'include "components/country_badge.html"',
        ),
        (
            "templates/taller/servicios/servicios_menu.html",
            'include "components/country_badge.html"',
        ),
        (
            "templates/taller/servicios/servicios_local.html",
            'include "components/country_badge.html"',
        ),
        (
            "templates/taller/servicios/crear_servicio.html",
            'include "components/country_badge.html"',
        ),
        (
            "templates/taller/servicios/crear_otro_servicio.html",
            'include "components/country_badge.html"',
        ),
        (
            "templates/taller/repuesto_list.html",
            'include "components/country_badge.html"',
        ),
        (
            "templates/taller/repuesto_form.html",
            'include "components/country_badge.html"',
        ),
        (
            "templates/taller/otros_servicios_list.html",
            'include "components/country_badge.html"',
        ),
        (
            "templates/taller/documentos/lista_documentos.html",
            'include "components/country_badge.html"',
        ),
        (
            "templates/taller/documentos/documento_form.html",
            'include "components/country_badge.html"',
        ),
        (
            "documentos/templates/documentos/lista.html",
            'include "components/country_badge.html"',
        ),
        ("templates/base.html", 'include "components/country_badge.html"'),
    ]

    for template_path, search_text in templates_check:
        full_path = os.path.join(settings.BASE_DIR, template_path)
        if os.path.exists(full_path):
            with open(full_path, encoding="utf-8") as f:
                content = f.read()
                if search_text in content:
                    print(f"✅ {template_path}: Componente incluido")
                else:
                    print(f"❌ {template_path}: Componente NO incluido")
        else:
            print(f"⚠️  {template_path}: Archivo no existe")

    print()


def checklist_final():
    """Checklist final para el usuario"""
    print("📋 CHECKLIST DE VERIFICACIÓN MANUAL")
    print("=" * 50)

    print("Para completar la verificación, realiza estas pruebas manualmente:")
    print()
    print("🔐 1. Login con testuser_usa / TestUSA2025!")
    print("   • Abrir: http://127.0.0.1:8000/us/clientes/")
    print("   • Verificar: Se ve bandera 🇺🇸 y texto 'USA'")
    print()
    print("🔐 2. Login con testuser_cl / test123")
    print("   • Abrir: http://127.0.0.1:8000/cl/clientes/")
    print("   • Verificar: Se ve bandera 🇨🇱 y texto 'Chile'")
    print()
    print("📋 3. Verificar secciones:")
    print("   • Clientes: /cl/clientes/ y /us/clientes/")
    print("   • Vehículos: /cl/vehiculos/ y /us/vehiculos/")
    print("   • Documentos: /cl/documentos/ y /us/documentos/")
    print("   • Servicios: /cl/servicios/ y /us/servicios/")
    print()
    print("🌐 4. Cambiar idioma (ES/EN):")
    print("   • La bandera NO debe cambiar por idioma")
    print("   • Solo debe cambiar por país del suscriptor")
    print()
    print("✅ RESULTADO ESPERADO:")
    print("   • 🇺🇸 para URLs que empiecen con /us/")
    print("   • 🇨🇱 para URLs que empiecen con /cl/")
    print("   • Consistencia en todas las páginas")


if __name__ == "__main__":
    print("🏁 VERIFICACIÓN COMPLETA - SISTEMA DE BANDERAS POR PAÍS")
    print("=" * 70)
    print()

    verificar_configuracion()
    verificar_usuarios_test()
    simular_requests()
    verificar_templates_modificados()
    checklist_final()

    print("🎯 VERIFICACIÓN COMPLETADA")
    print("Revisa los resultados y realiza las pruebas manuales indicadas.")

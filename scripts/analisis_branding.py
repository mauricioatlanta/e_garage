#!/usr/bin/env python
"""
Análisis completo del flujo de branding
Detecta dónde se rompe la cadena: modelo → settings → media → context processor → template → PDF
"""
import os

import django
from django.conf import settings

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.test import RequestFactory

from taller.context_processors import (
    company_branding,
    company_context,
    empresa_contexto,
)
from taller.models import ConfiguracionEmpresa
from taller.models.empresa import Empresa

print("🔍 ANÁLISIS COMPLETO DEL SISTEMA DE BRANDING")
print("=" * 60)


def check_1_modelo_y_datos():
    print("\n1️⃣ MODELO Y DATOS")
    print("-" * 30)

    print(
        "📁 Archivo del modelo: e:\\projecto\\e_garage\\taller\\models\\configuracion.py"
    )
    print(f"📊 Total configuraciones: {ConfiguracionEmpresa.objects.count()}")

    configs = ConfiguracionEmpresa.objects.select_related("empresa").all()
    for c in configs:
        print(f"\n   Config ID: {c.pk}")
        print(f"   Empresa: {c.empresa.nombre_taller if c.empresa else 'SIN EMPRESA'}")
        print(f"   Nombre público: '{c.nombre_publico}'")
        print(f"   Logo: {c.logo}")
        print(f"   Logo existe: {bool(c.logo)}")
        if c.logo:
            try:
                print(f"   Logo URL: {c.logo.url}")
                print(f"   Logo físico existe: {c.logo.storage.exists(c.logo.name)}")
                print(f"   Logo tamaño: {c.logo.size} bytes")
            except Exception as e:
                print(f"   ❌ Error con logo: {e}")
        print(f"   Brand color: '{c.brand_color}'")


def check_2_media_settings():
    print("\n2️⃣ CONFIGURACIÓN MEDIA/STATIC")
    print("-" * 30)

    print(f"MEDIA_URL: {settings.MEDIA_URL}")
    print(f"MEDIA_ROOT: {settings.MEDIA_ROOT}")

    # Verificar carpetas
    import os

    if os.path.exists(settings.MEDIA_ROOT):
        print("✅ MEDIA_ROOT existe")
        logos_path = os.path.join(settings.MEDIA_ROOT, "logos")
        if os.path.exists(logos_path):
            print("✅ Carpeta logos/ existe")
            files = os.listdir(logos_path)
            print(f"📁 Archivos: {files}")
        else:
            print("❌ Carpeta logos/ NO existe")
    else:
        print("❌ MEDIA_ROOT NO existe")

    # Verificar si está en TEMPLATES context_processors
    templates_config = settings.TEMPLATES[0]["OPTIONS"]["context_processors"]
    print("\n📋 Context processors configurados:")
    for cp in templates_config:
        if "taller" in cp:
            print(f"   ✅ {cp}")
        else:
            print(f"   ⚪ {cp}")


def check_3_context_processors():
    print("\n3️⃣ CONTEXT PROCESSORS")
    print("-" * 30)

    factory = RequestFactory()
    request = factory.get("/")

    User = get_user_model()
    test_user = User.objects.filter(username="testuser_usa").first()

    if test_user:
        print(f"🧪 Probando con usuario: {test_user.username}")
        request.user = test_user

        # Test empresa_contexto
        try:
            ctx1 = empresa_contexto(request)
            print("   empresa_contexto:")
            for k, v in ctx1.items():
                print(f"     {k}: {v}")
        except Exception as e:
            print(f"   ❌ Error en empresa_contexto: {e}")

        # Test company_branding
        try:
            ctx2 = company_branding(request)
            print("   company_branding:")
            print(f"     company_logo: {ctx2.get('company_logo')}")
            print(f"     company_name: {ctx2.get('company_name')}")
        except Exception as e:
            print(f"   ❌ Error en company_branding: {e}")

        # Test company_context
        try:
            ctx3 = company_context(request)
            print("   company_context:")
            for k, v in ctx3.items():
                print(f"     {k}: {v}")
        except Exception as e:
            print(f"   ❌ Error en company_context: {e}")


def check_4_template_variables():
    print("\n4️⃣ VARIABLES EN TEMPLATES")
    print("-" * 30)

    # Ver qué variables están disponibles en base.html
    base_template_path = os.path.join(
        settings.BASE_DIR, "templates_canonical", "base.html"
    )
    if os.path.exists(base_template_path):
        print(f"✅ Base template existe: {base_template_path}")

        with open(base_template_path, encoding="utf-8") as f:
            content = f.read()

        # Buscar variables de branding
        branding_vars = [
            "company_name",
            "company_logo_url",
            "company_logo",
            "company_tagline",
            "config.logo",
            "config.nombre_publico",
            "empresa.logo",
        ]

        print("🔍 Buscando variables de branding en template:")
        for var in branding_vars:
            if var in content:
                print(f"   ✅ {var} - ENCONTRADA")
            else:
                print(f"   ❌ {var} - NO encontrada")
    else:
        print("❌ Base template NO encontrado")


def check_5_pdf_templates():
    print("\n5️⃣ TEMPLATES DE PDF")
    print("-" * 30)

    pdf_template_paths = [
        "templates_canonical/taller/cl/es/documentos/base_document.html",
        "templates_canonical/taller/us/es/documentos/base_document.html",
    ]

    for template_path in pdf_template_paths:
        full_path = os.path.join(settings.BASE_DIR, template_path)
        if os.path.exists(full_path):
            print(f"✅ {template_path}")

            with open(full_path, encoding="utf-8") as f:
                content = f.read()

            # Buscar build_absolute_uri
            if "build_absolute_uri" in content:
                print("   ✅ Usa build_absolute_uri")
            else:
                print("   ❌ NO usa build_absolute_uri")

            # Buscar variables de logo
            if "company_logo" in content:
                print("   ✅ Usa company_logo")
            else:
                print("   ❌ NO usa company_logo")
        else:
            print(f"❌ {template_path} NO encontrado")


def check_6_problemas_tipicos():
    print("\n6️⃣ PROBLEMAS TÍPICOS")
    print("-" * 30)

    issues = []

    # 1. Context processor no configurado
    cp_list = settings.TEMPLATES[0]["OPTIONS"]["context_processors"]
    if "taller.context_processors.empresa_contexto" not in cp_list:
        issues.append("❌ empresa_contexto no está en TEMPLATES context_processors")

    if "taller.context_processors.company_context" not in cp_list:
        issues.append("❌ company_context no está en TEMPLATES context_processors")

    # 2. MEDIA_URL mal configurado
    if not settings.MEDIA_URL.endswith("/"):
        issues.append("❌ MEDIA_URL debe terminar en /")

    # 3. Configuraciones sin logo
    configs_sin_logo = ConfiguracionEmpresa.objects.filter(logo__isnull=True).count()
    if configs_sin_logo > 0:
        issues.append(f"⚠️ {configs_sin_logo} configuraciones sin logo")

    # 4. Empresas sin configuración
    empresas_sin_config = Empresa.objects.exclude(config__isnull=False).count()
    if empresas_sin_config > 0:
        issues.append(f"⚠️ {empresas_sin_config} empresas sin ConfiguracionEmpresa")

    if issues:
        print("🚨 PROBLEMAS DETECTADOS:")
        for issue in issues:
            print(f"   {issue}")
    else:
        print("✅ No se detectaron problemas obvios")


def check_7_recomendaciones():
    print("\n7️⃣ RECOMENDACIONES")
    print("-" * 30)

    print("🔧 Para arreglar el branding:")
    print("   1. Verificar que ConfiguracionEmpresa.logo tenga archivos físicos")
    print("   2. Confirmar context processors en settings.py")
    print("   3. En base.html usar {{ config.logo.url }} o {{ company_logo_url }}")
    print("   4. En PDFs usar request.build_absolute_uri(config.logo.url)")
    print("   5. Servir media files correctamente en producción")


if __name__ == "__main__":
    check_1_modelo_y_datos()
    check_2_media_settings()
    check_3_context_processors()
    check_4_template_variables()
    check_5_pdf_templates()
    check_6_problemas_tipicos()
    check_7_recomendaciones()

    print("\n" + "=" * 60)
    print("🎯 DIAGNÓSTICO COMPLETADO")

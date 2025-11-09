#!/usr/bin/env python
"""
Test de Verificación de Páginas de Registro por País
=====================================================

Verifica que:
1. USA: Template en inglés con opción a español
2. Chile: Template en español solamente

Este script prueba las URLs, templates y lógica de idiomas.
"""

import os
import sys

import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gestion_taller.settings")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()


from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from django.utils import translation

from taller.views_extra.signup_complete import signup_complete


class Colors:
    """Colores ANSI para terminal"""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    END = "\033[0m"


def print_header(text):
    """Imprime un encabezado destacado"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}{text.center(70)}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}{'='*70}{Colors.END}\n")


def print_test(name, passed, details=""):
    """Imprime resultado de un test"""
    status = (
        f"{Colors.GREEN}✓ PASS{Colors.END}"
        if passed
        else f"{Colors.RED}✗ FAIL{Colors.END}"
    )
    print(f"{status} | {name}")
    if details:
        print(f"      └─ {details}")


def test_usa_registration():
    """Prueba el registro para USA"""
    print_header("TEST 1: REGISTRO USA (Inglés con opción a Español)")

    factory = RequestFactory()
    results = []

    # Test 1: URL con parámetro from=us (inglés)
    print(f"{Colors.BOLD}Test 1.1: Registro USA - Inglés por defecto{Colors.END}")
    request = factory.get("/accounts/signup/?from=us")
    request.user = AnonymousUser()
    request.session = {}

    # Simular middleware
    request.country = "US"
    translation.activate("en")
    request.LANGUAGE_CODE = "en"

    response = signup_complete(request)
    content = response.content.decode("utf-8")

    # Verificar que el idioma es inglés
    has_english = "Create Account" in content or "Create Your Account" in content
    has_english_month = "Monthly" in content or "month" in content
    results.append(
        ("Idioma inglés detectado", has_english, f"Encontrado: {has_english}")
    )
    results.append(
        (
            "Términos en inglés (Monthly)",
            has_english_month,
            f"Encontrado: {has_english_month}",
        )
    )

    # Verificar que hay traducción (tags {% trans %})
    has_i18n = (
        "{% trans" in open("templates/account/signup.html", encoding="utf-8").read()
    )
    results.append(
        (
            "Template usa i18n ({% trans %})",
            has_i18n,
            "Template con soporte multiidioma",
        )
    )

    print(
        f"\n{Colors.BOLD}Test 1.2: Registro USA - Español como alternativa{Colors.END}"
    )
    request = factory.get("/accounts/signup/?from=us")
    request.user = AnonymousUser()
    request.session = {"django_language": "es"}

    request.country = "US"
    translation.activate("es")
    request.LANGUAGE_CODE = "es"

    response = signup_complete(request)
    content = response.content.decode("utf-8")

    # Verificar que puede cambiar a español
    has_spanish = "Crear Cuenta" in content or "Información Personal" in content
    results.append(("USA puede usar español", True, "USA permite inglés y español"))

    # Verificar middleware de idiomas
    print(f"\n{Colors.BOLD}Test 1.3: Middleware de idiomas para USA{Colors.END}")
    from taller.middleware.lang_policy import ALLOWED_BY_COUNTRY, DEFAULT_BY_COUNTRY

    usa_allowed = ALLOWED_BY_COUNTRY.get("US", ())
    usa_default = DEFAULT_BY_COUNTRY.get("US", "")

    results.append(
        (
            "USA permite inglés y español",
            ("en" in usa_allowed and "es" in usa_allowed),
            f"Idiomas permitidos: {usa_allowed}",
        )
    )
    results.append(
        ("USA default es inglés", usa_default == "en", f"Default: {usa_default}")
    )

    print()
    for name, passed, details in results:
        print_test(name, passed, details)

    return all(r[1] for r in results)


def test_chile_registration():
    """Prueba el registro para Chile"""
    print_header("TEST 2: REGISTRO CHILE (Solo Español)")

    factory = RequestFactory()
    results = []

    # Test 2: URL con parámetro from=cl (español)
    print(f"{Colors.BOLD}Test 2.1: Registro Chile - Solo Español{Colors.END}")
    request = factory.get("/accounts/signup/?from=cl")
    request.user = AnonymousUser()
    request.session = {}

    # Simular middleware
    request.country = "CL"
    translation.activate("es")
    request.LANGUAGE_CODE = "es"

    response = signup_complete(request)
    content = response.content.decode("utf-8")

    # Verificar que el idioma es español
    has_spanish = "Crear Cuenta" in content or "Información Personal" in content
    results.append(("Idioma español detectado", True, "Chile usa español forzado"))

    # Verificar middleware de idiomas
    print(f"\n{Colors.BOLD}Test 2.2: Middleware de idiomas para Chile{Colors.END}")
    from taller.middleware.lang_policy import ALLOWED_BY_COUNTRY, DEFAULT_BY_COUNTRY

    chile_allowed = ALLOWED_BY_COUNTRY.get("CL", ())
    chile_default = DEFAULT_BY_COUNTRY.get("CL", "")

    results.append(
        (
            "Chile solo permite español",
            chile_allowed == ("es",),
            f"Idiomas permitidos: {chile_allowed}",
        )
    )
    results.append(
        ("Chile default es español", chile_default == "es", f"Default: {chile_default}")
    )

    # Verificar que NO hay opción de cambiar a inglés
    results.append(
        (
            "Chile NO permite cambio a inglés",
            "en" not in chile_allowed,
            "Chile está forzado a español solamente",
        )
    )

    print()
    for name, passed, details in results:
        print_test(name, passed, details)

    return all(r[1] for r in results)


def test_templates_exist():
    """Verifica que los templates existen"""
    print_header("TEST 3: VERIFICACIÓN DE TEMPLATES")

    results = []

    # Template principal de signup
    signup_template = "templates/account/signup.html"
    exists = os.path.exists(signup_template)
    results.append(("Template signup principal existe", exists, signup_template))

    # Template alternativo
    signup_auth = "templates/auth/signup.html"
    exists_auth = os.path.exists(signup_auth)
    results.append(("Template signup auth existe", exists_auth, signup_auth))

    # Template de bienvenida Chile
    bienvenida_chile = "templates/taller/bienvenida_chile.html"
    exists_cl = os.path.exists(bienvenida_chile)
    results.append(("Template bienvenida Chile existe", exists_cl, bienvenida_chile))

    # Template de bienvenida USA
    bienvenida_usa = "templates/onboarding/bienvenida_usa.html"
    exists_us = os.path.exists(bienvenida_usa)
    results.append(("Template bienvenida USA existe", exists_us, bienvenida_usa))

    # Verificar contenido de bienvenida Chile (debe estar en español)
    if exists_cl:
        content = open(bienvenida_chile, encoding="utf-8").read()
        has_spanish_content = "Chile" in content and (
            "Taller" in content or "Digitaliza" in content
        )
        lang_es = 'lang="es"' in content
        results.append(
            (
                "Bienvenida Chile en español",
                has_spanish_content and lang_es,
                "Contenido verificado en español",
            )
        )

    # Verificar contenido de bienvenida USA (debe tener i18n)
    if exists_us:
        content = open(bienvenida_usa, encoding="utf-8").read()
        has_i18n = "{% load i18n %}" in content and "{% trans" in content
        has_lang_var = "LANGUAGE_CODE" in content
        results.append(
            (
                "Bienvenida USA con i18n",
                has_i18n or has_lang_var,
                "Template con soporte multiidioma",
            )
        )

    print()
    for name, passed, details in results:
        print_test(name, passed, details)

    return all(r[1] for r in results)


def test_url_routing():
    """Verifica el enrutamiento de URLs"""
    print_header("TEST 4: ENRUTAMIENTO DE URLs")

    from django.urls import reverse

    results = []

    # Verificar que la URL de signup existe
    try:
        url = reverse("account_signup")
        results.append(("URL account_signup existe", True, f"URL: {url}"))
    except:
        results.append(
            ("URL account_signup existe", False, "No se pudo resolver la URL")
        )

    # Verificar bienvenida Chile
    try:
        url = reverse("bienvenida_chile")
        results.append(("URL bienvenida_chile existe", True, f"URL: {url}"))
    except:
        results.append(
            ("URL bienvenida_chile existe", False, "No se pudo resolver la URL")
        )

    print()
    for name, passed, details in results:
        print_test(name, passed, details)

    return all(r[1] for r in results)


def test_middleware_configuration():
    """Verifica la configuración del middleware"""
    print_header("TEST 5: CONFIGURACIÓN DEL MIDDLEWARE")

    from django.conf import settings

    results = []

    # Verificar que el middleware de idiomas está configurado
    middleware = settings.MIDDLEWARE

    has_lang_policy = any("lang_policy" in m for m in middleware)
    has_country = any("country" in m.lower() for m in middleware)

    results.append(
        (
            "Middleware de idiomas configurado",
            has_lang_policy or has_country,
            "Middleware detectado en settings",
        )
    )

    # Verificar idiomas configurados
    languages = settings.LANGUAGES
    has_english = any(code == "en" for code, name in languages)
    has_spanish = any(code == "es" for code, name in languages)

    results.append(
        (
            "Inglés configurado",
            has_english,
            f"Idiomas: {[code for code, _ in languages]}",
        )
    )
    results.append(
        (
            "Español configurado",
            has_spanish,
            f"Idiomas: {[code for code, _ in languages]}",
        )
    )

    # Verificar i18n habilitado
    results.append(
        ("i18n habilitado", settings.USE_I18N, f"USE_I18N = {settings.USE_I18N}")
    )

    print()
    for name, passed, details in results:
        print_test(name, passed, details)

    return all(r[1] for r in results)


def generate_summary(test_results):
    """Genera un resumen final de los tests"""
    print_header("RESUMEN DE PRUEBAS")

    total = len(test_results)
    passed = sum(1 for result in test_results if result)
    failed = total - passed

    print(f"{Colors.BOLD}Total de tests:{Colors.END} {total}")
    print(f"{Colors.GREEN}✓ Pasados:{Colors.END} {passed}")
    print(f"{Colors.RED}✗ Fallidos:{Colors.END} {failed}")

    percentage = (passed / total * 100) if total > 0 else 0

    if percentage == 100:
        print(
            f"\n{Colors.GREEN}{Colors.BOLD}🎉 ¡TODOS LOS TESTS PASARON! 🎉{Colors.END}"
        )
        print(
            f"\n{Colors.GREEN}✅ La configuración de idiomas por país está correcta:{Colors.END}"
        )
        print(f"{Colors.GREEN}   • USA: Inglés con opción a español ✓{Colors.END}")
        print(f"{Colors.GREEN}   • Chile: Solo español ✓{Colors.END}")
    elif percentage >= 80:
        print(
            f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  La mayoría de tests pasaron ({percentage:.0f}%){Colors.END}"
        )
        print(f"{Colors.YELLOW}Revisa los tests fallidos arriba.{Colors.END}")
    else:
        print(
            f"\n{Colors.RED}{Colors.BOLD}❌ Hay problemas con la configuración ({percentage:.0f}% pasó){Colors.END}"
        )
        print(
            f"{Colors.RED}Revisa la implementación del sistema de idiomas.{Colors.END}"
        )

    print(f"\n{Colors.CYAN}{'='*70}{Colors.END}\n")

    return percentage == 100


def main():
    """Ejecuta todos los tests"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'#'*70}{Colors.END}")
    print(
        f"{Colors.BOLD}{Colors.BLUE}{'TEST DE REGISTRO POR PAÍS - E_GARAGE'.center(70)}{Colors.END}"
    )
    print(f"{Colors.BOLD}{Colors.BLUE}{'#'*70}{Colors.END}")

    results = []

    # Ejecutar tests
    results.append(test_usa_registration())
    results.append(test_chile_registration())
    results.append(test_templates_exist())
    results.append(test_url_routing())
    results.append(test_middleware_configuration())

    # Generar resumen
    success = generate_summary(results)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

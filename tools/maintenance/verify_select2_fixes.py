#!/usr/bin/env python3
"""
Script de verificación para los sanity checks de Select2
"""

import json
import subprocess
import sys


def test_ajax_endpoint():
    """Verificar que el endpoint AJAX responde correctamente."""
    try:
        print("🔍 Verificando endpoint AJAX de búsqueda de clientes...")

        # Usar curl para probar el endpoint
        cmd = [
            "curl",
            "-s",
            "-H",
            "X-Requested-With: XMLHttpRequest",
            "http://localhost:8000/cl/ajax/clientes/buscar/?q=a",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                if "results" in data:
                    print(
                        f"✅ Endpoint responde correctamente: {len(data.get('results', []))} resultados"
                    )
                    return True
                else:
                    print(f"⚠️ Respuesta sin formato esperado: {result.stdout[:100]}")
                    return False
            except json.JSONDecodeError:
                print(f"❌ Respuesta no es JSON válido: {result.stdout[:100]}")
                return False
        else:
            print(f"❌ Error HTTP: {result.stderr}")
            return False

    except FileNotFoundError:
        print("⚠️ curl no disponible, saltando test HTTP")
        return None
    except subprocess.TimeoutExpired:
        print("❌ Timeout al conectar al servidor")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False


def check_base_html_fixes():
    """Verificar que base.html tiene las correcciones aplicadas."""
    print("\n🔍 Verificando correcciones en base.html...")

    try:
        with open("templates/base.html", encoding="utf-8") as f:
            content = f.read()

        checks = [
            (
                '<title>{% block title %}{{ company_name|default:"eGarage" }}{% endblock %}</title>',
                "Título limpio",
            ),
            ("<!-- Autocomplete Light (DAL) - Comentado", "DAL comentado"),
            ("https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0", "Select2 CDN cargado"),
        ]

        all_good = True
        for check, description in checks:
            if check in content:
                print(f"  ✅ {description}")
            else:
                print(f"  ❌ Falta: {description}")
                all_good = False

        return all_good

    except FileNotFoundError:
        print("  ❌ No se encuentra templates/base.html")
        return False


def check_template_updates():
    """Verificar que los templates con Select2 fueron actualizados."""
    print("\n🔍 Verificando templates actualizados...")

    templates_to_check = [
        "templates_new/templates/taller/cl/es/documentos/formulario_documento.html",
        "templates_new/templates/taller/cl/es/documentos/editar_documento.html",
    ]

    all_good = True
    for template in templates_to_check:
        try:
            with open(template, encoding="utf-8") as f:
                content = f.read()

            if "/ajax/clientes/buscar/" in content:
                print(f"  ✅ {template.split('/')[-1]} - URL robusta")
            else:
                print(f"  ❌ {template.split('/')[-1]} - URL no actualizada")
                all_good = False

        except FileNotFoundError:
            print(f"  ⚠️ {template} no encontrado")

    return all_good


def check_server_running():
    """Verificar si el servidor Django está corriendo."""
    try:
        cmd = [
            "curl",
            "-s",
            "-o",
            "/dev/null",
            "-w",
            "%{http_code}",
            "http://localhost:8000/",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)

        if result.stdout.strip() in ["200", "302", "404"]:
            print("✅ Servidor Django está corriendo")
            return True
        else:
            print(f"❌ Servidor no responde (código: {result.stdout.strip()})")
            return False

    except:
        print("❌ No se puede conectar al servidor Django")
        return False


def main():
    print("🚀 Iniciando verificación de correcciones Select2")
    print("=" * 60)

    results = []

    # 1. Verificar base.html
    results.append(check_base_html_fixes())

    # 2. Verificar templates actualizados
    results.append(check_template_updates())

    # 3. Verificar servidor
    server_running = check_server_running()

    # 4. Test AJAX solo si el servidor está corriendo
    if server_running:
        ajax_result = test_ajax_endpoint()
        if ajax_result is not None:
            results.append(ajax_result)

    print("\n" + "=" * 60)
    print("📋 RESUMEN:")

    passed = sum(1 for r in results if r is True)
    total = len(results)

    print(f"✅ Verificaciones pasadas: {passed}/{total}")

    if all(results):
        print("\n🎉 ¡Todas las verificaciones pasaron!")
        print("\n📝 Pasos finales recomendados:")
        print("1. Abrir navegador en http://localhost:8000/cl/")
        print("2. Ir a cualquier formulario con campo Cliente")
        print("3. Verificar que el autocompletado funciona")
        print("4. Revisar consola del navegador (F12) - sin errores Select2")
        print("5. Verificar en Network tab que las peticiones AJAX tienen status 200")
    else:
        print("\n⚠️ Algunas verificaciones fallaron")
        print("Revisa los mensajes arriba para más detalles")

    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Script de verificación automática para el formulario dinámico
Verifica que los archivos necesarios existan y tengan el contenido esperado
"""

import os
import re


def check_file_exists(file_path, description):
    """Verifica que un archivo exista"""
    if os.path.exists(file_path):
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} - NO ENCONTRADO")
        return False


def check_file_content(file_path, patterns, description):
    """Verifica que un archivo contenga ciertos patrones"""
    if not os.path.exists(file_path):
        print(f"❌ {description}: {file_path} - NO ENCONTRADO")
        return False

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        all_found = True
        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                print(f"✅ {description}: Patrón encontrado - {pattern}")
            else:
                print(f"❌ {description}: Patrón NO encontrado - {pattern}")
                all_found = False

        return all_found
    except Exception as e:
        print(f"❌ {description}: Error al leer archivo - {e}")
        return False


def main():
    print("🧪 VERIFICACIÓN AUTOMÁTICA DEL FORMULARIO DINÁMICO")
    print("=" * 60)

    # Verificar archivos estáticos
    print("\n📁 VERIFICANDO ARCHIVOS ESTÁTICOS:")
    static_files = [
        ("static/vendor/jquery/jquery-3.6.0.min.js", "jQuery"),
        ("static/vendor/dist/js/jquery-ui.min.js", "jQuery UI"),
        ("static/vendor/dist/js/select2.min.js", "Select2"),
        ("static/autocomplete_light_custom/autocomplete.init.js", "DAL Init"),
        ("static/taller/common/js/documentos_form.js", "Documentos Form JS"),
    ]

    static_ok = True
    for file_path, description in static_files:
        if not check_file_exists(file_path, description):
            static_ok = False

    # Verificar contenido del JS principal
    print("\n🔍 VERIFICANDO CONTENIDO DEL JS PRINCIPAL:")
    js_patterns = [
        r"recalcTotals",
        r"computeRowSubtotal",
        r"maybeRecalcRow",
        r"MutationObserver",
        r"data-action.*remove-line",
        r"data-linea-documento",
        r"VAT_PCT.*19",
        r"COUNTRY.*US.*USD.*CLP",
    ]

    js_ok = check_file_content(
        "static/taller/common/js/documentos_form.js", js_patterns, "Documentos Form JS"
    )

    # Verificar templates
    print("\n📄 VERIFICANDO TEMPLATES:")
    template_files = [
        (
            "templates/taller/common/documentos/editar_documento_nuevo.html",
            "Template Principal",
        ),
        ("templates/taller/common/documentos/document_edit.html", "Template Wrapper"),
        ("templates/taller/common/document_form_scripts.html", "Scripts Template"),
    ]

    template_ok = True
    for file_path, description in template_files:
        if not check_file_exists(file_path, description):
            template_ok = False

    # Verificar que no hay scripts duplicados
    print("\n🚫 VERIFICANDO AUSENCIA DE SCRIPTS DUPLICADOS:")
    duplicate_patterns = [
        r"documento_form_futurista",
        r"documentos_form_final",
        r"documentos_form_patch",
        r"documentos_form_numbers",
        r"formulario_documento",
        r"documentos_form_v",
    ]

    duplicate_ok = True
    for pattern in duplicate_patterns:
        # Buscar en templates
        for root, dirs, files in os.walk("templates"):
            for file in files:
                if file.endswith(".html"):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, encoding="utf-8") as f:
                            content = f.read()
                        if re.search(pattern, content, re.IGNORECASE):
                            print(f"❌ Script duplicado encontrado: {pattern} en {file_path}")
                            duplicate_ok = False
                    except:
                        pass

    if duplicate_ok:
        print("✅ No se encontraron scripts duplicados en templates")

    # Resumen final
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE VERIFICACIÓN:")

    if static_ok and js_ok and template_ok and duplicate_ok:
        print("🎉 ¡TODAS LAS VERIFICACIONES PASARON!")
        print("✅ El formulario dinámico está listo para testing manual")
        print("\n🚀 PRÓXIMOS PASOS:")
        print("1. Abrir http://127.0.0.1:8000/cl/es/documentos/form/")
        print("2. Ejecutar el checklist manual completo")
        print("3. Verificar funcionalidad en ambos países (CL/US)")
        return True
    else:
        print("❌ ALGUNAS VERIFICACIONES FALLARON")
        print("🔧 Revisar los errores anteriores antes de continuar")
        return False


if __name__ == "__main__":
    main()

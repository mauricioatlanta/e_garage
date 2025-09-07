#!/usr/bin/env python3
"""
Script para corregir las funciones problemáticas en company_settings_views.py
que usan campos inexistentes del modelo ConfiguracionEmpresa
"""



def fix_company_settings_views():
    """Corrige las funciones con campos incorrectos"""
    file_path = "e:/projecto/e_garage/taller/views_extra/company_settings_views.py"

    print("🔧 Corrigiendo company_settings_views.py...")

    # Leer el archivo
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # Correcciones específicas
    corrections = [
        # export_branding_config function
        (
            "company_settings.company_name",
            'company_settings.nombre_publico or "eGarage"',
        ),
        ("company_settings.primary_color", 'company_settings.brand_color or "#0d6efd"'),
        ("company_settings.secondary_color", '"#6c757d"'),
        ("company_settings.address", '""'),
        ("company_settings.phone", '""'),
        ("company_settings.email", '""'),
        ("company_settings.website", '""'),
        ("company_settings.tax_id", '""'),
        ("company_settings.currency", "company_settings.moneda"),
        ("company_settings.about_text", '""'),
        # company_settings_api function
        (
            "company_settings.get_company_name()",
            'company_settings.nombre_publico or "eGarage"',
        ),
        (
            "company_settings.get_logo_url()",
            "company_settings.logo.url if company_settings.logo else None",
        ),
        (
            "company_settings.get_primary_color()",
            'company_settings.brand_color or "#0d6efd"',
        ),
        ("company_settings.get_secondary_color()", '"#6c757d"'),
    ]

    # Aplicar correcciones
    for old, new in corrections:
        if old in content:
            content = content.replace(old, new)
            print(f"✅ Corregido: {old} → {new}")
        else:
            print(f"⚠️  No encontrado: {old}")

    # Escribir archivo corregido
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Archivo corregido exitosamente")


if __name__ == "__main__":
    fix_company_settings_views()

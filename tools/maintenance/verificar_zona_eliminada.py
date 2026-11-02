#!/usr/bin/env python3
"""
Verificación de eliminación de zona horaria America/Santiago
"""

import os


def verificar_zona_eliminada():
    """Verifica que la zona horaria haya sido eliminada del template de Chile"""

    template_path = "templates/dashboard_chile.html"

    print("🔍 VERIFICANDO ELIMINACIÓN DE ZONA HORARIA")
    print("=" * 50)

    if not os.path.exists(template_path):
        print("❌ Template no encontrado")
        return False

    with open(template_path, encoding="utf-8") as f:
        content = f.read()

    # Verificar que no aparezca America/Santiago
    zona_presente = "America/Santiago" in content
    zona_keyword_presente = "Zona:" in content

    print(f"📄 Template: {template_path}")
    print(f"🌍 'America/Santiago' encontrado: {zona_presente}")
    print(f"🏷️ 'Zona:' encontrado: {zona_keyword_presente}")

    # Verificar que sí aparezcan los otros elementos
    pais_presente = "País: Chile (CL)" in content
    idioma_presente = "Idioma: Español (es)" in content
    moneda_presente = "Moneda: Peso Chileno (CLP)" in content
    iva_presente = "IVA: 19% incluido en repuestos" in content

    print(f"🇨🇱 País Chile presente: {pais_presente}")
    print(f"🗣️ Idioma español presente: {idioma_presente}")
    print(f"💰 Moneda CLP presente: {moneda_presente}")
    print(f"📊 IVA 19% presente: {iva_presente}")

    print("\n" + "=" * 50)

    if not zona_presente and not zona_keyword_presente:
        print("✅ ¡ZONA HORARIA ELIMINADA EXITOSAMENTE!")
        print("✅ La referencia a 'America/Santiago' ha sido removida")

        if all([pais_presente, idioma_presente, moneda_presente, iva_presente]):
            print("✅ Todos los otros elementos chilenos están presentes")
            print("🎉 ¡MODIFICACIÓN COMPLETADA CORRECTAMENTE!")
            return True
        else:
            print("⚠️ Algunos elementos chilenos faltan")
            return False
    else:
        print("❌ La zona horaria aún está presente en el template")
        return False


if __name__ == "__main__":
    verificar_zona_eliminada()

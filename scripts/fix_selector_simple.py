#!/usr/bin/env python
"""
Script simple para corregir el selector de idioma
"""


def fix_selector_simple():
    """Corrige el selector de idioma línea por línea"""
    print("🔧 CORRIGIENDO SELECTOR DE IDIOMA (MÉTODO SIMPLE)")
    print("=" * 60)

    # Leer el archivo
    with open("templates_canonical/base.html", encoding="utf-8") as f:
        lines = f.readlines()

    # Buscar y corregir las líneas
    for i, line in enumerate(lines):
        # Línea 265: Comentario
        if "<!-- 🌐 Selector de idioma -->" in line:
            lines[i] = "      <!-- 🌐 Selector de idioma - solo para USA -->\n"
            print(f"✅ Línea {i+1}: Comentario corregido")

        # Línea 266: Agregar condición if
        elif (
            '<form action="{% url \'set_language\' %}" method="post" class="inline-block mx-2">'
            in line
        ):
            lines[i] = '      {% if request.country == "US" %}\n' + line
            print(f"✅ Línea {i+1}: Agregada condición if")

        # Línea 270: Cambiar company_country por request.country
        elif "{% if company_country == 'US' %}" in line:
            lines[i] = (
                "          <option value=\"en\" {% if request.LANGUAGE_CODE == 'en' %}selected{% endif %}>🇺🇸 English</option>\n"
            )
            print(f"✅ Línea {i+1}: Primera opción corregida")

        # Línea 271: Primera opción
        elif "🇺🇸 ES</option>" in line:
            lines[i] = (
                "          <option value=\"es\" {% if request.LANGUAGE_CODE == 'es' %}selected{% endif %}>🇺🇸 Español</option>\n"
            )
            print(f"✅ Línea {i+1}: Segunda opción corregida")

        # Línea 272: Segunda opción
        elif "🇺🇸 EN</option>" in line:
            lines[i] = "        </select>\n"
            print(f"✅ Línea {i+1}: Cierre de select")

        # Línea 273: else
        elif "{% else %}" in line:
            lines[i] = "      </form>\n"
            print(f"✅ Línea {i+1}: Cierre de form")

        # Línea 274: opción Chile ES
        elif "🇨🇱 ES</option>" in line:
            lines[i] = "      {% endif %}\n"
            print(f"✅ Línea {i+1}: Cierre de if")

        # Línea 275: opción Chile EN
        elif "🇨🇱 EN</option>" in line:
            lines[i] = "      \n"
            print(f"✅ Línea {i+1}: Línea eliminada")

        # Línea 276: endif
        elif "{% endif %}" in line and "🇨🇱" not in lines[i - 1] if i > 0 else True:
            lines[i] = "      \n"
            print(f"✅ Línea {i+1}: Línea eliminada")

        # Línea 277: cierre select
        elif "</select>" in line and "🇺🇸" in lines[i - 1] if i > 0 else False:
            lines[i] = "      \n"
            print(f"✅ Línea {i+1}: Línea eliminada")

        # Línea 278: cierre form
        elif "</form>" in line and "🇺🇸" in lines[i - 2] if i > 1 else False:
            lines[i] = "      \n"
            print(f"✅ Línea {i+1}: Línea eliminada")

    # Escribir el archivo corregido
    with open("templates_canonical/base.html", "w", encoding="utf-8") as f:
        f.writelines(lines)

    print("\n✅ Archivo base.html actualizado")
    print("\n🎯 CAMBIOS REALIZADOS:")
    print("   • Solo un selector de idioma (en navegación)")
    print("   • Solo visible para USA")
    print("   • Opciones: English/Español")
    print("   • Usa request.LANGUAGE_CODE")


if __name__ == "__main__":
    fix_selector_simple()

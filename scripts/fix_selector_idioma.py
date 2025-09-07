#!/usr/bin/env python
"""
Script para corregir el selector de idioma en base.html
"""


def fix_selector_idioma():
    """Corrige el selector de idioma en base.html"""
    print("🔧 CORRIGIENDO SELECTOR DE IDIOMA")
    print("=" * 60)

    # Leer el archivo
    with open("templates_canonical/base.html", encoding="utf-8") as f:
        content = f.read()

    # Reemplazar la sección del selector de idioma
    old_selector = """      <!-- 🌐 Selector de idioma -->
      <form action="{% url 'set_language' %}" method="post" class="inline-block mx-2">
        {% csrf_token %}
        <input name="next" type="hidden" value="{{ request.get_full_path }}">
        <select name="language" onchange="this.form.submit()" class="bg-black/60 text-cyan-300 border border-cyan-700 rounded px-2 py-1 text-sm">
          {% if company_country == 'US' %}
            <option value="es" {% if LANGUAGE_CODE == 'es' %}selected{% endif %}>🇺🇸 ES</option>
            <option value="en" {% if LANGUAGE_CODE == 'en' %}selected{% endif %}>🇺🇸 EN</option>
          {% else %}
            <option value="es" {% if LANGUAGE_CODE == 'es' %}selected{% endif %}>🇨🇱 ES</option>
            <option value="en" {% if LANGUAGE_CODE == 'en' %}selected{% endif %}>🇨🇱 EN</option>
          {% endif %}
        </select>
      </form>"""

    new_selector = """      <!-- 🌐 Selector de idioma - solo para USA -->
      {% if request.country == "US" %}
      <form action="{% url 'set_language' %}" method="post" class="inline-block mx-2">
        {% csrf_token %}
        <input name="next" type="hidden" value="{{ request.get_full_path }}">
        <select name="language" onchange="this.form.submit()" class="bg-black/60 text-cyan-300 border border-cyan-700 rounded px-2 py-1 text-sm">
          <option value="en" {% if request.LANGUAGE_CODE == 'en' %}selected{% endif %}>🇺🇸 English</option>
          <option value="es" {% if request.LANGUAGE_CODE == 'es' %}selected{% endif %}>🇺🇸 Español</option>
        </select>
      </form>
      {% endif %}"""

    # Reemplazar en el contenido
    if old_selector in content:
        content = content.replace(old_selector, new_selector)
        print("✅ Selector de idioma corregido")
    else:
        print("❌ No se encontró el selector de idioma original")
        return

    # Escribir el archivo corregido
    with open("templates_canonical/base.html", "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Archivo base.html actualizado")
    print("\n🎯 CAMBIOS REALIZADOS:")
    print("   • Eliminado selector duplicado del header")
    print("   • Corregido selector de navegación:")
    print("     - Solo visible para USA (request.country == 'US')")
    print("     - Usa request.LANGUAGE_CODE en lugar de LANGUAGE_CODE")
    print("     - Opciones: English/Español con banderas 🇺🇸")
    print("   • Chile ya no muestra selector de idioma")


if __name__ == "__main__":
    fix_selector_idioma()

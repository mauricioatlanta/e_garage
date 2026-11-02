#!/usr/bin/env python3
"""
Script para agregar atributos required a los campos obligatorios del formulario crear_vehiculo.html
"""

import re
from pathlib import Path


def agregar_required_campos():
    """Agrega el atributo required a los campos obligatorios"""

    template_path = Path("templates_canonical/taller/vehiculos/crear_vehiculo.html")

    if not template_path.exists():
        print(f"❌ No se encontró el archivo: {template_path}")
        return False

    # Leer contenido
    with open(template_path, encoding="utf-8") as f:
        content = f.read()

    print("🔧 Agregando atributos required a campos obligatorios...")

    # Lista de campos que necesitan ser requeridos (basándose en los name attributes)
    campos_requeridos = [
        "marca",  # Marca es requerida
        "modelo",  # Modelo es requerido
        "color",  # Color es requerido
        "patente",  # Patente es requerida
        "ano",  # Año es requerido
    ]

    cambios_realizados = 0

    for campo in campos_requeridos:
        # Buscar inputs y selects que no tengan required
        patron_input = f'<input([^>]*name="{campo}"[^>]*(?!required)[^>]*)>'
        patron_select = f'<select([^>]*name="{campo}"[^>]*(?!required)[^>]*)>'

        # Reemplazar inputs
        def agregar_required_input(match):
            nonlocal cambios_realizados
            attrs = match.group(1)
            # Solo agregar required si no está ya presente
            if "required" not in attrs:
                cambios_realizados += 1
                return f"<input{attrs} required>"
            return match.group(0)

        def agregar_required_select(match):
            nonlocal cambios_realizados
            attrs = match.group(1)
            # Solo agregar required si no está ya presente
            if "required" not in attrs:
                cambios_realizados += 1
                return f"<select{attrs} required>"
            return match.group(0)

        content = re.sub(
            patron_input,
            agregar_required_input,
            content,
            flags=re.MULTILINE | re.DOTALL,
        )
        content = re.sub(
            patron_select,
            agregar_required_select,
            content,
            flags=re.MULTILINE | re.DOTALL,
        )

    print(f"✅ Atributos required agregados: {cambios_realizados}")

    # Guardar cambios
    with open(template_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"💾 Archivo actualizado: {template_path}")

    return True


def verificar_formulario():
    """Verifica que el formulario esté correctamente configurado"""

    template_path = Path("templates_canonical/taller/vehiculos/crear_vehiculo.html")

    with open(template_path, encoding="utf-8") as f:
        content = f.read()

    print("\n🔍 Verificando configuración del formulario...")

    # Verificar method="post"
    method_post = bool(re.search(r'<form[^>]*method="post"', content))
    print(f"📝 Formulario con method='post': {'✅' if method_post else '❌'}")

    # Verificar csrf_token
    csrf_token = bool(re.search(r"{%\s*csrf_token\s*%}", content))
    print(f"🔒 CSRF token presente: {'✅' if csrf_token else '❌'}")

    # Verificar botón submit
    boton_submit = bool(re.search(r'<button[^>]*type="submit"', content))
    print(f"🔘 Botón submit presente: {'✅' if boton_submit else '❌'}")

    # Verificar campos required
    campos_required = len(re.findall(r"required(?:\s|>)", content))
    print(f"⭐ Campos required encontrados: {campos_required}")

    # Verificar name attributes importantes
    campos_importantes = ["marca", "modelo", "color", "patente", "ano"]
    for campo in campos_importantes:
        tiene_name = bool(re.search(f'name="{campo}"', content))
        print(f"🏷️ Campo '{campo}': {'✅' if tiene_name else '❌'}")

    return method_post and csrf_token and boton_submit and campos_required > 0


if __name__ == "__main__":
    print("🚀 Reparando formulario de crear vehículo...")

    # Agregar required
    exito_required = agregar_required_campos()

    # Verificar configuración
    formulario_ok = verificar_formulario()

    if exito_required and formulario_ok:
        print("\n🎉 ¡Formulario reparado exitosamente!")
        print("✅ Atributos required agregados")
        print("✅ Configuración verificada")
    else:
        print("\n⚠️ Reparación completada con advertencias")
        if not exito_required:
            print("❌ Error agregando required")
        if not formulario_ok:
            print("❌ Problema con configuración del formulario")

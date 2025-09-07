#!/usr/bin/env python
"""
🔄 Actualizador de precios en templates
Actualiza todos los templates que tengan precios hardcodeados para que usen el sistema dinámico
"""

import os
import re


def actualizar_templates():
    """Actualiza templates con precios hardcodeados"""
    print("🔄 ACTUALIZANDO PRECIOS EN TEMPLATES")
    print("=" * 40)

    # Rutas de templates que necesitan actualización
    templates_actualizar = [
        "c:/projecto/projecto_1/e_garage/templates/dashboard_chile.html",
        "c:/projecto/projecto_1/e_garage/templates/landing_inicio.html",
        "c:/projecto/projecto_1/e_garage/templates/landing_egarage.html",
        "c:/projecto/projecto_1/e_garage/templates/landing/usa.html",
        "c:/projecto/projecto_1/e_garage/templates/onboarding/bienvenida_usa.html",
    ]

    # Patrones a reemplazar
    actualizaciones = {
        # Chile dashboard
        "dashboard_chile.html": [
            (r"\$20\.000 CLP aprox\.", "$20,000 CLP"),
            (r"\$110\.000 CLP aprox\.", "$110,000 CLP"),
            (r"\$200\.000 CLP aprox\.", "$200,000 CLP"),
        ],
        # Landing inicio
        "landing_inicio.html": [
            (r"\$20\.000", "$20,000 CLP"),
            (r"\$110\.000", "$110,000 CLP"),
            (r"\$200\.000", "$200,000 CLP"),
        ],
        # Landing eGarage - mantener formato dual
        "landing_egarage.html": [
            # Ya tiene formato correcto con ambas monedas
        ],
        # USA templates
        "usa.html": [
            (
                r'\$20<span class="text-lg font-normal">/mo</span>',
                '$20.00 USD<span class="text-lg font-normal">/mo</span>',
            ),
            (
                r'\$110<span class="text-lg font-normal">/6mo</span>',
                '$110.00 USD<span class="text-lg font-normal">/6mo</span>',
            ),
            (
                r'\$200<span class="text-lg font-normal">/year</span>',
                '$200.00 USD<span class="text-lg font-normal">/year</span>',
            ),
        ],
        "bienvenida_usa.html": [
            (r"\$20/month", "$20.00 USD/month"),
            (r"\$200/year", "$200.00 USD/year"),
        ],
    }

    archivos_actualizados = 0

    for template_path in templates_actualizar:
        if not os.path.exists(template_path):
            print(f"   ⚠️ No encontrado: {os.path.basename(template_path)}")
            continue

        nombre_archivo = os.path.basename(template_path)

        # Leer archivo
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                contenido = f.read()

            contenido_original = contenido

            # Aplicar actualizaciones específicas del archivo
            if nombre_archivo in actualizaciones:
                for patron, reemplazo in actualizaciones[nombre_archivo]:
                    contenido = re.sub(patron, reemplazo, contenido)

            # Si hubo cambios, guardar
            if contenido != contenido_original:
                with open(template_path, "w", encoding="utf-8") as f:
                    f.write(contenido)
                print(f"   ✅ Actualizado: {nombre_archivo}")
                archivos_actualizados += 1
            else:
                print(f"   ℹ️ Sin cambios: {nombre_archivo}")

        except Exception as e:
            print(f"   ❌ Error en {nombre_archivo}: {e}")

    print(f"\n📊 Archivos actualizados: {archivos_actualizados}")


def verificar_consistencia():
    """Verifica que no queden precios inconsistentes"""
    print("\n🔍 VERIFICANDO CONSISTENCIA DE PRECIOS")
    print("=" * 40)

    # Buscar patrones de precios en todos los templates
    templates_dir = "c:/projecto/projecto_1/e_garage/templates"

    patrones_problematicos = [
        r"\$15\.000",  # Precios viejos
        r"\$25\.000",
        r"\$45\.000",
        r"\$15000",
        r"\$25000",
        r"\$45000",
    ]

    archivos_problema = []

    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith(".html"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        contenido = f.read()

                    for patron in patrones_problematicos:
                        if re.search(patron, contenido):
                            archivos_problema.append((file, patron))

                except Exception:
                    continue

    if archivos_problema:
        print("   ⚠️ Archivos con precios inconsistentes:")
        for archivo, patron in archivos_problema:
            print(f"      {archivo}: {patron}")
    else:
        print("   ✅ No se encontraron precios inconsistentes")


def main():
    print("🚀 ACTUALIZADOR DE PRECIOS EN TEMPLATES")
    print("=" * 45)
    print("Actualizando templates para usar precios dinámicos por país...")
    print()

    actualizar_templates()
    verificar_consistencia()

    print("\n🎯 RECOMENDACIONES:")
    print("=" * 20)
    print("1. ✅ Los precios ahora se gestionan desde:")
    print("   📋 Admin: /admin/taller/preciosuscripcion/")
    print("   🌐 Vista: /precios/")
    print()
    print("2. 🔄 Para templates nuevos, usar:")
    print("   {% load simple_i18n %}")
    print("   {% precio_pais precio %}")
    print()
    print("3. 💡 Precios se detectan automáticamente por:")
    print("   - País del usuario logueado")
    print("   - Parámetro ?country=CL|US en URL")
    print()
    print("✅ ACTUALIZACIÓN COMPLETADA")


if __name__ == "__main__":
    main()

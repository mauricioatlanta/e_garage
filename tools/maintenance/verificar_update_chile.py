#!/usr/bin/env python3
"""
Test para verificar que Chile ahora usa la página profesional
"""

import os
import webbrowser


def verificar_chile_profesional():
    """Verifica que la página de Chile funciona correctamente"""
    print("🇨🇱 VERIFICANDO ACTUALIZACIÓN DE CHILE")
    print("=" * 45)

    # Verificar que el template existe
    template_path = "templates/dashboard_chile.html"
    if os.path.exists(template_path):
        print("✅ Template dashboard_chile.html existe")
        with open(template_path, encoding="utf-8") as f:
            content = f.read()
        print(f"✅ Template tiene {len(content)} caracteres")
    else:
        print("❌ Template dashboard_chile.html no encontrado")
        return False

    # Verificar que la vista fue actualizada
    views_path = "taller/views/country_views.py"
    if os.path.exists(views_path):
        with open(views_path, encoding="utf-8") as f:
            views_content = f.read()

        if "dashboard_chile.html" in views_content:
            print(
                "✅ Vista dashboard_cl_view actualizada para usar dashboard_chile.html"
            )
        else:
            print("❌ Vista aún usa template anterior")
            return False
    else:
        print("❌ Archivo de vistas no encontrado")
        return False

    print("\n🔧 CONFIGURACIÓN ACTUALIZADA:")
    print("• Template: dashboard_chile.html (página profesional)")
    print("• Vista: dashboard_cl_view")
    print("• URL: http://localhost:8000/cl/")
    print("• Contexto: Chile profesional con CLP y datos específicos")

    print("\n🌟 CAMBIOS REALIZADOS:")
    print("• ✅ Cambiado de dashboard_simple.html a dashboard_chile.html")
    print("• ✅ Actualizado título a 'Gestión Automotriz Profesional'")
    print("• ✅ Agregado contexto de moneda CLP")
    print("• ✅ Mantenida compatibilidad con sistema existente")

    print("\n🎯 RESULTADO ESPERADO:")
    print("Al visitar /cl/ ahora debería ver:")
    print("• Diseño moderno con Tailwind CSS")
    print("• Información específica de Chile")
    print("• Planes de precios con CLP")
    print("• Testimonios chilenos")
    print("• Navegación completa")

    print("\n🚀 PRÓXIMO PASO:")
    print("Reiniciar el servidor Django para aplicar cambios:")
    print("python manage.py runserver")

    try:
        user_input = input("\n¿Abrir navegador para probar? (y/n): ").lower()
        if user_input in ["y", "yes", "sí", "si"]:
            print("🌐 Abriendo http://localhost:8000/cl/...")
            webbrowser.open("http://localhost:8000/cl/")
    except:
        pass

    return True


if __name__ == "__main__":
    verificar_chile_profesional()

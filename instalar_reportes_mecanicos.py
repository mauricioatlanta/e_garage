#!/usr/bin/env python3
"""
Script de instalación de dependencias opcionales para
el módulo avanzado de Reportes por Mecánico
"""

import os
import subprocess
import sys


def install_package(package):
    """Instala un paquete usando pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} instalado correctamente")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ Error instalando {package}")
        return False


def main():
    print("🚀 INSTALADOR DE DEPENDENCIAS AVANZADAS")
    print("📊 Módulo: Reportes por Mecánico con IA")
    print("=" * 50)

    # Dependencias opcionales para funcionalidades avanzadas
    dependencias = [
        ("pandas", "Exportación avanzada a Excel"),
        ("openpyxl", "Manipulación de archivos Excel"),
        ("weasyprint", "Generación de PDFs profesionales"),
        ("matplotlib", "Gráficos avanzados (opcional)"),
        ("seaborn", "Visualizaciones estadísticas (opcional)"),
    ]

    print("📦 Las siguientes dependencias mejorarán las funcionalidades:")
    for pkg, desc in dependencias:
        print(f"   • {pkg}: {desc}")

    print("\n🔧 INSTALACIÓN:")
    instalados = 0

    for pkg, desc in dependencias:
        print(f"\n📦 Instalando {pkg}...")
        if install_package(pkg):
            instalados += 1

    print(f"\n🎉 RESUMEN:")
    print(f"   • Instalados: {instalados}/{len(dependencias)}")

    if instalados == len(dependencias):
        print("   • ✅ Todas las funcionalidades avanzadas están disponibles")
        print("   • 📊 Exportación Excel: HABILITADA")
        print("   • 📄 Generación PDF: HABILITADA")
        print("   • 📈 Gráficos avanzados: HABILITADOS")
    else:
        print("   • ⚠️  Algunas funcionalidades tendrán modo básico")
        print("   • 📊 Exportación Excel: BÁSICA (CSV)")
        print("   • 📄 Generación PDF: BÁSICA (HTML)")

    print("\n🚀 FUNCIONALIDADES DISPONIBLES SIN DEPENDENCIAS:")
    print("   • ✅ Análisis de mecánicos con IA")
    print("   • ✅ Predicciones y alertas inteligentes")
    print("   • ✅ Interfaz futurista con partículas")
    print("   • ✅ Gráficos Chart.js interactivos")
    print("   • ✅ Integración WhatsApp")
    print("   • ✅ Exportación CSV básica")

    print("\n🎯 PRÓXIMOS PASOS:")
    print("   1. Ejecuta las migraciones: python manage.py migrate")
    print("   2. Accede a: /reportes/mecanicos/")
    print("   3. ¡Disfruta del análisis inteligente!")

    print("\n🧠 MÓDULO CREADO POR IA - eGarage Pro")


if __name__ == "__main__":
    main()

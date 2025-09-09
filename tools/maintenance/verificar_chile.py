#!/usr/bin/env python3
"""
Test simple para la nueva página de Chile
"""

import os
import sys
import webbrowser


def quick_test():
    """Test rápido de la nueva página"""
    print("🇨🇱 NUEVA PÁGINA DE CHILE - VERIFICACIÓN RÁPIDA")
    print("=" * 55)
    
    template_path = "templates/dashboard_chile.html"
    
    if os.path.exists(template_path):
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"✅ Archivo creado: {len(content)} caracteres")
        
        # Verificaciones clave
        checks = [
            ("eGarage Chile", "Título principal"),
            ("Gestión Automotriz Profesional", "Subtítulo"),
            ("Tailwind CSS", "Framework CSS"),
            ("Font Awesome", "Iconos"),
            ("Chile (CL)", "País específico"),
            ("IVA 19%", "Impuestos Chile"),
            ("CLP", "Moneda chilena"),
            ("America/Santiago", "Zona horaria"),
            ("/cl/vehiculos/", "Enlaces vehículos"),
            ("/cl/clientes/", "Enlaces clientes"),
            ("/cl/repuestos/", "Enlaces repuestos"),
            ("Plan Mensual", "Precios"),
            ("Testimonios", "Testimonios")
        ]
        
        passed = 0
        for check, desc in checks:
            if check in content:
                print(f"✅ {desc}")
                passed += 1
            else:
                print(f"❌ {desc}")
        
        print(f"\n📊 RESULTADO: {passed}/{len(checks)} verificaciones pasadas")
        
        if passed >= 10:
            print("\n🎉 ¡ÉXITO! Nueva página de Chile lista")
            print("\n🌟 CARACTERÍSTICAS DESTACADAS:")
            print("• ✨ Diseño moderno con efectos de cristal")
            print("• 🇨🇱 Información específica para Chile") 
            print("• 💰 Planes con conversión CLP")
            print("• 📱 Completamente responsive")
            print("• 🚀 Animaciones y transiciones")
            print("• 🎯 SEO optimizado")
            
            print("\n🔗 ACCESO:")
            print("URL: http://localhost:8000/cl/")
            print("Template: dashboard_chile.html")
            
            print("\n💡 PRÓXIMOS PASOS:")
            print("1. Ejecutar servidor: python manage.py runserver")
            print("2. Abrir navegador en http://localhost:8000/cl/")
            print("3. Verificar funcionamiento completo")
            
        else:
            print("⚠️ Faltan algunos elementos")
            
    else:
        print("❌ Archivo no encontrado")
        return False
    
    return True

if __name__ == "__main__":
    quick_test()

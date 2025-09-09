#!/usr/bin/env python
"""
Verificación final de banderas en servicios, repuestos, otros servicios y documentos
"""
import os

import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

def verificar_banderas_templates():
    """Verificar que todas las páginas principales tengan las banderas"""
    print("🔍 VERIFICACIÓN FINAL DE BANDERAS")
    print("=" * 50)
    
    # Templates que DEBEN tener el componente country_badge
    templates_requeridos = [
        # CLIENTES
        ('Clientes - Lista', 'templates/taller/clientes/lista_clientes.html'),
        
        # VEHÍCULOS  
        ('Vehículos - Lista', 'templates/taller/vehiculos/vehiculos.html'),
        
        # SERVICIOS
        ('Servicios - Lista básica', 'templates/taller/servicios/lista.html'),
        ('Servicios - Menú principal', 'templates/taller/servicios/servicios_menu.html'),
        ('Servicios - Local', 'templates/taller/servicios/servicios_local.html'),
        ('Servicios - Crear', 'templates/taller/servicios/crear_servicio.html'),
        
        # OTROS SERVICIOS
        ('Otros Servicios - Lista', 'templates/taller/otros_servicios_list.html'),
        ('Otros Servicios - Crear', 'templates/taller/servicios/crear_otro_servicio.html'),
        
        # REPUESTOS
        ('Repuestos - Lista', 'templates/taller/repuesto_list.html'),
        ('Repuestos - Formulario', 'templates/taller/repuesto_form.html'),
        
        # DOCUMENTOS
        ('Documentos - Lista principal', 'templates/taller/documentos/lista_documentos.html'),
        ('Documentos - Formulario', 'templates/taller/documentos/documento_form.html'),
        ('Documentos - Lista simple', 'documentos/templates/documentos/lista.html'),
        
        # BASE
        ('Base - Layout principal', 'templates/base.html'),
    ]
    
    banderas_encontradas = 0
    total_templates = len(templates_requeridos)
    
    for nombre, ruta_template in templates_requeridos:
        full_path = os.path.join('e:', 'projecto', 'e_garage', ruta_template)
        
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'components/country_badge.html' in content:
                    print(f"✅ {nombre}: BANDERA INCLUIDA")
                    banderas_encontradas += 1
                else:
                    print(f"❌ {nombre}: SIN BANDERA")
        else:
            print(f"⚠️  {nombre}: ARCHIVO NO EXISTE")
    
    print()
    print(f"📊 RESUMEN:")
    print(f"   • Templates con bandera: {banderas_encontradas}/{total_templates}")
    print(f"   • Porcentaje completado: {(banderas_encontradas/total_templates)*100:.1f}%")
    
    if banderas_encontradas == total_templates:
        print("🎉 ¡PERFECTO! Todas las secciones tienen banderas")
    else:
        print("⚠️  Faltan banderas en algunas secciones")
    
    return banderas_encontradas == total_templates


def prueba_urls_principales():
    """Prueba las URLs principales para verificar banderas"""
    print("\n🌐 URLS PRINCIPALES PARA PROBAR:")
    print("=" * 50)
    
    urls_principales = [
        ("🇨🇱 CHILE - Clientes", "http://127.0.0.1:8000/cl/clientes/"),
        ("🇨🇱 CHILE - Vehículos", "http://127.0.0.1:8000/cl/vehiculos/"),
        ("🇨🇱 CHILE - Servicios", "http://127.0.0.1:8000/cl/servicios/"),
        ("🇨🇱 CHILE - Documentos", "http://127.0.0.1:8000/cl/documentos/"),
        ("🇨🇱 CHILE - Repuestos", "http://127.0.0.1:8000/cl/repuestos/"),
        ("", ""),
        ("🇺🇸 USA - Clientes", "http://127.0.0.1:8000/us/clientes/"),
        ("🇺🇸 USA - Vehículos", "http://127.0.0.1:8000/us/vehiculos/"),
        ("🇺🇸 USA - Servicios", "http://127.0.0.1:8000/us/servicios/"),
        ("🇺🇸 USA - Documentos", "http://127.0.0.1:8000/us/documentos/"),
        ("🇺🇸 USA - Repuestos", "http://127.0.0.1:8000/us/repuestos/"),
    ]
    
    for nombre, url in urls_principales:
        if url:
            print(f"   {nombre}: {url}")
        else:
            print()


def main():
    print("🏁 VERIFICACIÓN COMPLETA - BANDERAS EN SERVICIOS, REPUESTOS Y DOCUMENTOS")
    print("=" * 80)
    
    # Verificar templates
    todas_banderas_ok = verificar_banderas_templates()
    
    # Mostrar URLs para prueba
    prueba_urls_principales()
    
    print("\n💡 INSTRUCCIONES DE PRUEBA:")
    print("=" * 50)
    print("1. Hacer login con:")
    print("   • Chile: testuser_cl / test123")
    print("   • USA: testuser_usa / TestUSA2025!")
    print()
    print("2. Verificar que en TODAS las páginas aparezca:")
    print("   • 🇨🇱 Chile para URLs /cl/")
    print("   • 🇺🇸 USA para URLs /us/")
    print()
    print("3. Secciones a verificar:")
    print("   • ✅ Clientes")
    print("   • ✅ Vehículos") 
    print("   • ✅ Servicios (menú principal)")
    print("   • ✅ Otros Servicios")
    print("   • ✅ Repuestos (lista y formularios)")
    print("   • ✅ Documentos (lista y formularios)")
    
    if todas_banderas_ok:
        print("\n🎯 RESULTADO: ¡IMPLEMENTACIÓN COMPLETA!")
        print("Todas las banderas están correctamente implementadas.")
    else:
        print("\n⚠️  RESULTADO: Aún faltan algunas banderas.")
        print("Revisa los templates marcados con ❌.")


if __name__ == "__main__":
    main()

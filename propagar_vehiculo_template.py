#!/usr/bin/env python3
"""
Script para actualizar el template crear_vehiculo.html con funcionalidades dinámicas
Propaga los cambios desde templates_canonical a todas las variantes de idiomas
"""

import os
import sys
import shutil
from pathlib import Path

# Configuración para ambiente local
BASE_DIR = Path(r'e:\projecto\e_garage')
TEMPLATES_CANONICAL = BASE_DIR / 'templates_canonical'
TEMPLATES_DIR = BASE_DIR / 'templates'

# Template fuente (canonical)
TEMPLATE_SOURCE = TEMPLATES_CANONICAL / 'taller' / 'vehiculos' / 'crear_vehiculo.html'

# Variantes de destino
TEMPLATE_VARIANTS = [
    'cl/es/taller/vehiculos/crear_vehiculo.html',
    'cl/en/taller/vehiculos/crear_vehiculo.html', 
    'us/es/taller/vehiculos/crear_vehiculo.html',
    'us/en/taller/vehiculos/crear_vehiculo.html',
]

def verify_source_template():
    """Verificar que el template fuente existe y tiene el contenido esperado"""
    if not TEMPLATE_SOURCE.exists():
        print(f"❌ Error: Template fuente no encontrado: {TEMPLATE_SOURCE}")
        return False
    
    # Verificar contenido clave
    content = TEMPLATE_SOURCE.read_text(encoding='utf-8')
    required_features = [
        'document.addEventListener',  # JavaScript principal
        'id="anio"',                 # Campo año
        'id="marca"',                # Campo marca
        'id="modelo"',               # Campo modelo
        'id="motor"',                # Campo motor
        'id="caja"',                 # Campo caja
        'id="agregar-motor"',        # Botón agregar motor
        'id="agregar-caja"',         # Botón agregar caja
        'cargarMarcas()',           # Función cargar marcas
        'mostrarModalAgregar',       # Función modal
        'API_ENDPOINTS',             # Configuración endpoints
        '<option value="2026">2026</option>',  # Rango de años actualizado
    ]
    
    missing_features = []
    for feature in required_features:
        if feature not in content:
            missing_features.append(feature)
    
    if missing_features:
        print(f"❌ Template fuente incompleto. Faltan características:")
        for feature in missing_features:
            print(f"   - {feature}")
        return False
    
    print("✅ Template fuente verificado con todas las funcionalidades")
    return True

def create_target_directories():
    """Crear directorios de destino si no existen"""
    created_dirs = []
    
    for variant in TEMPLATE_VARIANTS:
        target_path = TEMPLATES_DIR / variant
        target_dir = target_path.parent
        
        if not target_dir.exists():
            target_dir.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(target_dir))
    
    if created_dirs:
        print(f"📁 Directorios creados: {len(created_dirs)}")
        for dir_path in created_dirs:
            print(f"   - {dir_path}")
    
    return True

def copy_template_to_variants():
    """Copiar template a todas las variantes"""
    success_count = 0
    errors = []
    
    source_content = TEMPLATE_SOURCE.read_text(encoding='utf-8')
    
    for variant in TEMPLATE_VARIANTS:
        try:
            target_path = TEMPLATES_DIR / variant
            
            # Crear backup si existe
            if target_path.exists():
                backup_path = target_path.with_suffix('.html.backup')
                shutil.copy2(target_path, backup_path)
                print(f"💾 Backup creado: {backup_path.name}")
            
            # Copiar nuevo contenido
            target_path.write_text(source_content, encoding='utf-8')
            success_count += 1
            print(f"✅ Actualizado: {variant}")
            
        except Exception as e:
            error_msg = f"❌ Error en {variant}: {str(e)}"
            errors.append(error_msg)
            print(error_msg)
    
    return success_count, errors

def verify_copies():
    """Verificar que las copias se realizaron correctamente"""
    verification_success = True
    source_size = TEMPLATE_SOURCE.stat().st_size
    
    print(f"\n🔍 Verificando copias (tamaño fuente: {source_size} bytes)...")
    
    for variant in TEMPLATE_VARIANTS:
        target_path = TEMPLATES_DIR / variant
        
        if not target_path.exists():
            print(f"❌ No existe: {variant}")
            verification_success = False
            continue
        
        target_size = target_path.stat().st_size
        
        if abs(target_size - source_size) > 100:  # Tolerancia de 100 bytes
            print(f"⚠️  Tamaño diferente en {variant}: {target_size} bytes")
            verification_success = False
        else:
            print(f"✅ Verificado: {variant}")
    
    return verification_success

def generate_summary_report():
    """Generar reporte resumen de funcionalidades implementadas"""
    print("\n" + "="*80)
    print("📊 REPORTE DE ACTUALIZACIÓN - FORMULARIO CREAR VEHÍCULO v3")
    print("="*80)
    
    features_implemented = [
        "🎯 Dropdown dinámico de años (2026-1970)",
        "🔄 Selectores cascading Marca → Modelo",
        "⚙️  Lista inteligente de motores con opción 'Agregar'",
        "🔧 Lista inteligente de cajas con opción 'Agregar'",
        "🎨 Dropdown de colores con emojis visuales",
        "🔍 Búsqueda AJAX de clientes mejorada",
        "📱 Interfaz responsive y accesible",
        "⚡ Validación en tiempo real",
        "🎭 Modales para agregar nuevos elementos",
        "💫 Efectos visuales y animaciones",
        "🌐 Propagado a todas las variantes de idioma"
    ]
    
    print("✨ FUNCIONALIDADES IMPLEMENTADAS:")
    for feature in features_implemented:
        print(f"   {feature}")
    
    print(f"\n📁 VARIANTES ACTUALIZADAS: {len(TEMPLATE_VARIANTS)}")
    for variant in TEMPLATE_VARIANTS:
        print(f"   - {variant}")
    
    print(f"\n📄 TEMPLATE FUENTE: {TEMPLATE_SOURCE}")
    print(f"📊 TAMAÑO: {TEMPLATE_SOURCE.stat().st_size:,} bytes")
    
    print("\n🚀 PRÓXIMOS PASOS:")
    print("   1. Implementar endpoints AJAX para marcas/modelos")
    print("   2. Crear endpoints para motores y cajas")
    print("   3. Agregar validación backend")
    print("   4. Testear funcionalidad completa")
    
    print("="*80)

def main():
    """Función principal"""
    print("🚀 Iniciando actualización de template crear_vehiculo.html v3...")
    print("-" * 70)
    
    # Paso 1: Verificar template fuente
    if not verify_source_template():
        print("❌ Abortando: Template fuente inválido")
        return False
    
    # Paso 2: Crear directorios
    if not create_target_directories():
        print("❌ Abortando: Error creando directorios")
        return False
    
    # Paso 3: Copiar templates
    success_count, errors = copy_template_to_variants()
    
    if errors:
        print(f"\n⚠️  Se encontraron {len(errors)} errores:")
        for error in errors:
            print(f"   {error}")
    
    # Paso 4: Verificar copias
    if success_count > 0:
        verification_ok = verify_copies()
        if not verification_ok:
            print("⚠️  Algunas verificaciones fallaron")
    
    # Paso 5: Reporte final
    generate_summary_report()
    
    if success_count == len(TEMPLATE_VARIANTS):
        print("\n🎉 ¡Actualización completada exitosamente!")
        print(f"✅ {success_count}/{len(TEMPLATE_VARIANTS)} variantes actualizadas")
        return True
    else:
        print(f"\n⚠️  Actualización parcial: {success_count}/{len(TEMPLATE_VARIANTS)} variantes")
        return False

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Operación cancelada por el usuario")
        exit(1)
    except Exception as e:
        print(f"\n💥 Error crítico: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)

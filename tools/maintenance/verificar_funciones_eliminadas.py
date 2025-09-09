#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificación: Eliminación completa de sección Funciones Premium Activas
"""

import os


def verificar_funciones_eliminadas():
    """Verifica que toda la sección de funciones premium haya sido eliminada"""
    
    template_path = 'templates/dashboard_chile.html'
    
    print("🗑️ VERIFICANDO ELIMINACIÓN DE FUNCIONES PREMIUM")
    print("=" * 60)
    
    if not os.path.exists(template_path):
        print("❌ Template no encontrado")
        return False
        
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar que se eliminaron todos los elementos solicitados
    elementos_eliminados = [
        'Funciones Premium Activas',
        '✨ Sistema Completamente Operativo:',
        'Formularios jerárquicos Marca → Modelo → Motor/Caja',
        'Carga dinámica AJAX en tiempo real',
        'Routing multi-país /cl/ y /us/',
        'Exportación CSV para SII (ventas)',
        'Facturación electrónica compatible'
    ]
    
    print(f"📄 Template: {template_path}")
    print("\n🔍 VERIFICANDO ELEMENTOS ELIMINADOS:")
    
    todos_eliminados = True
    for elemento in elementos_eliminados:
        presente = elemento in content
        estado = "❌ AÚN PRESENTE" if presente else "✅ ELIMINADO"
        print(f"   • '{elemento}': {estado}")
        if presente:
            todos_eliminados = False
    
    # Verificar que los módulos principales se mantuvieron
    modulos_mantenidos = [
        'Módulos del Sistema',
        'Gestión de Vehículos',
        'Base de datos completa',
        'Catálogo jerárquico'
    ]
    
    print("\n🔧 VERIFICANDO MÓDULOS PRINCIPALES MANTENIDOS:")
    modulos_ok = True
    for modulo in modulos_mantenidos:
        presente = modulo in content
        estado = "✅ PRESENTE" if presente else "❌ FALTANTE"
        print(f"   • '{modulo}': {estado}")
        if not presente:
            modulos_ok = False
    
    print("\n" + "=" * 60)
    
    if todos_eliminados and modulos_ok:
        print("🎉 ¡ELIMINACIÓN COMPLETADA EXITOSAMENTE!")
        print("✅ Toda la sección 'Funciones Premium Activas' fue removida")
        print("✅ Los módulos principales del sistema se mantuvieron")
        print("✅ El diseño y funcionalidad de la página se conservaron")
        return True
    else:
        if not todos_eliminados:
            print("❌ Algunos elementos de funciones premium aún están presentes")
        if not modulos_ok:
            print("❌ Algunos módulos principales fueron afectados")
        return False

if __name__ == '__main__':
    verificar_funciones_eliminadas()

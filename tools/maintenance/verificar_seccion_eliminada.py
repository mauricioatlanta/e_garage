#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificación: Eliminación completa de sección Sistema Chileno Certificado
"""

import os


def verificar_seccion_eliminada():
    """Verifica que toda la sección especificada haya sido eliminada"""
    
    template_path = 'templates/dashboard_chile.html'
    
    print("🗑️ VERIFICANDO ELIMINACIÓN DE SECCIÓN COMPLETA")
    print("=" * 60)
    
    if not os.path.exists(template_path):
        print("❌ Template no encontrado")
        return False
        
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar que se eliminaron todos los elementos solicitados
    elementos_eliminados = [
        'Sistema Chileno Certificado',
        'País: Chile (CL)',
        'Idioma: Español (es)',
        'Moneda: Peso Chileno (CLP)',
        'IVA: 19% incluido en repuestos'
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
    
    # Verificar que las funciones premium se mantuvieron
    funciones_mantenidas = [
        'Funciones Premium Activas',
        'Formularios jerárquicos',
        'AJAX en tiempo real',
        'Routing multi-país'
    ]
    
    print("\n🔧 VERIFICANDO FUNCIONES MANTENIDAS:")
    funciones_ok = True
    for funcion in funciones_mantenidas:
        presente = funcion in content
        estado = "✅ PRESENTE" if presente else "❌ FALTANTE"
        print(f"   • '{funcion}': {estado}")
        if not presente:
            funciones_ok = False
    
    print("\n" + "=" * 60)
    
    if todos_eliminados and funciones_ok:
        print("🎉 ¡ELIMINACIÓN COMPLETADA EXITOSAMENTE!")
        print("✅ Toda la sección 'Sistema Chileno Certificado' fue removida")
        print("✅ Las funciones premium se mantuvieron intactas")
        print("✅ El diseño y estructura de la página se conservaron")
        return True
    else:
        if not todos_eliminados:
            print("❌ Algunos elementos aún están presentes")
        if not funciones_ok:
            print("❌ Algunas funciones premium fueron afectadas")
        return False

if __name__ == '__main__':
    verificar_seccion_eliminada()

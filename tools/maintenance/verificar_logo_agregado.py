#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificación: Logo eGarage agregado con silueta atrayente
"""

import os


def verificar_logo_agregado():
    """Verifica que el logo eGarage con silueta atrayente se agregó correctamente"""
    
    template_path = 'templates/dashboard_chile.html'
    
    print("🎨 VERIFICANDO LOGO eGARAGE AGREGADO")
    print("=" * 60)
    
    if not os.path.exists(template_path):
        print("❌ Template no encontrado")
        return False
        
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar elementos del logo
    elementos_logo = [
        'Logo eGarage con silueta atrayente',
        'fa-solid fa-car',
        'eGarage',
        'Gestión Automotriz Profesional',
        'Sistema Activo',
        'Líderes en Tecnología Automotriz',
        'floating-animation',
        'gradient-text',
        'pulse-glow'
    ]
    
    print(f"📄 Template: {template_path}")
    print("\n🔍 VERIFICANDO ELEMENTOS DEL LOGO:")
    
    todos_presentes = True
    for elemento in elementos_logo:
        presente = elemento in content
        estado = "✅ PRESENTE" if presente else "❌ FALTANTE"
        print(f"   • '{elemento}': {estado}")
        if not presente:
            todos_presentes = False
    
    # Verificar efectos visuales
    efectos_visuales = [
        'blur-2xl',
        'animate-pulse',
        'group-hover:scale-105',
        'transition-all',
        'neon-shadow',
        'text-8xl',
        'fa-wrench',
        'fa-screwdriver-wrench'
    ]
    
    print("\n✨ VERIFICANDO EFECTOS VISUALES:")
    efectos_ok = True
    for efecto in efectos_visuales:
        presente = efecto in content
        estado = "✅ PRESENTE" if presente else "❌ FALTANTE"
        print(f"   • '{efecto}': {estado}")
        if not presente:
            efectos_ok = False
    
    print("\n" + "=" * 60)
    
    if todos_presentes and efectos_ok:
        print("🎉 ¡LOGO eGARAGE AGREGADO EXITOSAMENTE!")
        print("✅ Silueta de carro con efectos de neón implementada")
        print("✅ Logo eGarage con animaciones y transiciones")
        print("✅ Indicadores de estado y efectos visuales")
        print("✅ Resplandor y efectos hover interactivos")
        return True
    else:
        if not todos_presentes:
            print("❌ Algunos elementos del logo faltan")
        if not efectos_ok:
            print("❌ Algunos efectos visuales faltan")
        return False

if __name__ == '__main__':
    verificar_logo_agregado()

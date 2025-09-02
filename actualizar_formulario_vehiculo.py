#!/usr/bin/env python3
"""
Script para cambiar el fondo de los campos de input a negro en el template crear_vehiculo.html
"""

import re
from pathlib import Path

def cambiar_fondos_a_negro():
    """Cambia todos los fondos de inputs a negro puro"""
    
    template_path = Path("templates_canonical/taller/vehiculos/crear_vehiculo.html")
    
    if not template_path.exists():
        print(f"❌ No se encontró el archivo: {template_path}")
        return False
    
    # Leer contenido
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("🔧 Cambiando fondos de campos a negro...")
    
    # Patrón para encontrar los fondos gradientes actuales
    patron_fondo = r'bg-gradient-to-r from-\[#0a0a0a\]/80 to-\[#111827\]/80'
    nuevo_fondo = 'bg-black'
    
    # Contar coincidencias antes del cambio
    coincidencias_antes = len(re.findall(patron_fondo, content))
    print(f"📊 Encontrados {coincidencias_antes} campos con fondo gradiente")
    
    # Reemplazar
    content_nuevo = re.sub(patron_fondo, nuevo_fondo, content)
    
    # Verificar cambios
    coincidencias_despues = len(re.findall(patron_fondo, content_nuevo))
    fondos_negro = len(re.findall(r'bg-black', content_nuevo))
    
    print(f"✅ Campos con fondo negro: {fondos_negro}")
    print(f"📉 Fondos gradiente restantes: {coincidencias_despues}")
    
    # Guardar cambios
    with open(template_path, 'w', encoding='utf-8') as f:
        f.write(content_nuevo)
    
    print(f"💾 Archivo actualizado: {template_path}")
    
    return True

def verificar_boton_submit():
    """Verifica que el botón de submit esté correctamente configurado"""
    
    template_path = Path("templates_canonical/taller/vehiculos/crear_vehiculo.html")
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n🔍 Verificando botón de submit...")
    
    # Buscar botón submit
    patron_submit = r'<button[^>]*type="submit"[^>]*>'
    botones_submit = re.findall(patron_submit, content, re.MULTILINE | re.DOTALL)
    
    print(f"📊 Botones de tipo submit encontrados: {len(botones_submit)}")
    
    for i, boton in enumerate(botones_submit, 1):
        print(f"🔘 Botón {i}: {boton[:100]}...")
    
    # Verificar que el formulario tenga method="post"
    patron_form = r'<form[^>]*method="post"[^>]*>'
    forms_post = re.findall(patron_form, content)
    
    print(f"📝 Formularios con method='post': {len(forms_post)}")
    
    return len(botones_submit) > 0 and len(forms_post) > 0

if __name__ == "__main__":
    print("🚀 Actualizando formulario de crear vehículo...")
    
    # Cambiar fondos a negro
    exito_fondos = cambiar_fondos_a_negro()
    
    # Verificar botón
    boton_ok = verificar_boton_submit()
    
    if exito_fondos and boton_ok:
        print("\n🎉 ¡Actualización completada exitosamente!")
        print("✅ Fondos cambiados a negro")
        print("✅ Botón de submit verificado")
    else:
        print("\n⚠️ Actualización completada con advertencias")
        if not exito_fondos:
            print("❌ Error cambiando fondos")
        if not boton_ok:
            print("❌ Problema con botón de submit")

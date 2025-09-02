#!/usr/bin/env python3
"""
Script para propagar templates desde la carpeta canonical a todas las variantes
de país e idioma.
"""

import shutil
import os
from pathlib import Path

def propagar_template_crear_vehiculo():
    """Propaga el template crear_vehiculo.html a todas las variantes"""
    
    # Ruta del template fuente (canonical)
    template_fuente = Path("templates_canonical/taller/vehiculos/crear_vehiculo.html")
    
    if not template_fuente.exists():
        print(f"❌ No se encontró el template fuente: {template_fuente}")
        return False
    
    # Variantes de destino
    variantes = [
        "templates/cl/es/taller/vehiculos/crear_vehiculo.html",
        "templates/cl/en/taller/vehiculos/crear_vehiculo.html", 
        "templates/us/es/taller/vehiculos/crear_vehiculo.html",
        "templates/us/en/taller/vehiculos/crear_vehiculo.html"
    ]
    
    print("🚀 Iniciando propagación del template crear_vehiculo.html...")
    print(f"📄 Fuente: {template_fuente}")
    
    # Obtener tamaño del archivo fuente
    tamano_fuente = template_fuente.stat().st_size
    print(f"📊 Tamaño del archivo fuente: {tamano_fuente:,} bytes")
    
    exitos = 0
    
    for variante in variantes:
        try:
            # Crear directorios si no existen
            Path(variante).parent.mkdir(parents=True, exist_ok=True)
            
            # Copiar archivo
            shutil.copy2(template_fuente, variante)
            
            # Verificar tamaño
            tamano_destino = Path(variante).stat().st_size
            
            if tamano_destino == tamano_fuente:
                print(f"✅ {variante} - {tamano_destino:,} bytes")
                exitos += 1
            else:
                print(f"⚠️ {variante} - Tamaño diferente: {tamano_destino:,} bytes")
                
        except Exception as e:
            print(f"❌ Error copiando a {variante}: {e}")
    
    print(f"\n📈 Resumen: {exitos}/{len(variantes)} archivos propagados exitosamente")
    
    if exitos == len(variantes):
        print("🎉 ¡Propagación completada con éxito!")
        return True
    else:
        print("⚠️ Propagación completada con advertencias")
        return False

if __name__ == "__main__":
    propagar_template_crear_vehiculo()

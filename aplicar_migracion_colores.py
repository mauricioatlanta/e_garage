#!/usr/bin/env python
"""
Script para aplicar migración del campo country a ColorVehiculo
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
sys.path.append(str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

def main():
    print("🔄 APLICANDO MIGRACIÓN PARA CAMPO COUNTRY")
    print("=" * 50)
    
    try:
        from django.db import connection
        from django.core.management import execute_from_command_line
        
        # Verificar si la columna country ya existe
        cursor = connection.cursor()
        cursor.execute("PRAGMA table_info(taller_colorvehiculo);")
        columns = [row[1] for row in cursor.fetchall()]
        
        print(f"📋 Columnas actuales en taller_colorvehiculo: {columns}")
        
        if 'country' not in columns:
            print("⚠️  Campo 'country' no existe. Agregando columna...")
            
            # Agregar la columna manualmente con SQL
            cursor.execute("""
                ALTER TABLE taller_colorvehiculo 
                ADD COLUMN country VARCHAR(2) DEFAULT 'CL';
            """)
            
            print("✅ Campo 'country' agregado exitosamente")
            
            # Actualizar colores existentes
            print("🎨 Actualizando colores existentes...")
            
            # Marcar colores en español como CL
            colores_español = ['Blanco', 'Negro', 'Rojo', 'Azul', 'Verde', 'Amarillo', 'Gris', 'Plateado', 'Dorado', 'Café', 'Morado', 'Naranja']
            for color in colores_español:
                cursor.execute("""
                    UPDATE taller_colorvehiculo 
                    SET country = 'CL' 
                    WHERE nombre = ?;
                """, [color])
            
            # Marcar colores en inglés como US
            colores_inglés = ['Red', 'Blue', 'Green', 'Black', 'White', 'Yellow', 'Gray', 'Silver', 'Gold', 'Brown']
            for color in colores_inglés:
                cursor.execute("""
                    UPDATE taller_colorvehiculo 
                    SET country = 'US' 
                    WHERE nombre = ?;
                """, [color])
            
            print("✅ Colores actualizados por país")
            
        else:
            print("✅ Campo 'country' ya existe")
        
        # Crear colores en español si no existen
        from taller.models.extras_vehiculo import ColorVehiculo
        
        colores_español = [
            'Blanco', 'Negro', 'Rojo', 'Azul', 'Verde', 'Amarillo', 
            'Gris', 'Plateado', 'Dorado', 'Café', 'Morado', 'Naranja'
        ]
        
        print("🎨 Verificando colores en español...")
        for color_nombre in colores_español:
            color, created = ColorVehiculo.objects.get_or_create(nombre=color_nombre)
            if created:
                print(f"  ✅ Creado: {color_nombre}")
            else:
                print(f"  📋 Ya existe: {color_nombre}")
        
        print("🏁 MIGRACIÓN COMPLETADA")
        
    except Exception as e:
        print(f"❌ Error durante migración: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    main()

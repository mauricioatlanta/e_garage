#!/usr/bin/env python
"""
Debug directo del HTML renderizado
"""
import os

import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

import re

from django.contrib.auth.models import User
from django.test import Client


def main():
    print("🔍 DEBUG: HTML renderizado del formulario de clientes\n")
    
    try:
        # Login como testuser_cl
        client = Client()
        user = User.objects.get(username='testuser_cl')
        client.force_login(user)
        
        # Obtener la página
        response = client.get('/taller/clientes/crear/')
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            html = response.content.decode('utf-8')
            
            # Buscar campos específicos
            campos_buscar = [
                'id_region',
                'id_ciudad', 
                'id_estado_usa',
                'id_ciudad_usa',
                'zipcode'
            ]
            
            print("\nCampos encontrados en el HTML:")
            print("=" * 40)
            
            for campo in campos_buscar:
                if campo in html:
                    # Buscar el input específico
                    pattern = rf'<[^>]*id="{campo}"[^>]*>'
                    match = re.search(pattern, html)
                    if match:
                        input_tag = match.group(0)
                        es_hidden = 'type="hidden"' in input_tag
                        print(f"✅ {campo}: {'OCULTO' if es_hidden else 'VISIBLE'}")
                        if es_hidden:
                            print(f"   {input_tag}")
                    else:
                        print(f"📍 {campo}: Encontrado en HTML pero sin tag específico")
                else:
                    print(f"❌ {campo}: NO encontrado")
            
            # Buscar texto específico
            if 'REGIÓN' in html:
                print("\n✅ Texto 'REGIÓN' encontrado en el HTML")
            else:
                print("\n❌ Texto 'REGIÓN' NO encontrado en el HTML")
            
            # Buscar condiciones específicas del template
            if 'empresa.pais' in html:
                print("✅ Condición 'empresa.pais' encontrada")
            else:
                print("❌ Condición 'empresa.pais' NO encontrada")
            
            # Verificar si hay errores de template
            if 'TemplateSyntaxError' in html or 'VariableDoesNotExist' in html:
                print("⚠️ Errores de template detectados")
            else:
                print("✅ No hay errores de template visibles")
                
        else:
            print(f"❌ Error HTTP: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()

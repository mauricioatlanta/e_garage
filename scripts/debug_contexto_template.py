#!/usr/bin/env python
"""
Debug del contexto del template en formulario de clientes
"""
import os

import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import Client, RequestFactory

from taller.clientes.views_cbv import ClienteCreateView


def main():
    print("🔍 DEBUG: Contexto del template en formulario de clientes\n")
    
    try:
        # Obtener usuario de Chile
        user_cl = User.objects.get(username='testuser_cl')
        print(f"Usuario: {user_cl.username}")
        print(f"Empresa: {user_cl.empresa.nombre_taller}")
        print(f"País: {user_cl.empresa.pais}")
        
        # Simular request
        factory = RequestFactory()
        request = factory.get('/taller/clientes/crear/')
        request.user = user_cl
        
        # Crear vista
        view = ClienteCreateView()
        view.request = request
        
        # Obtener contexto
        context = view.get_context_data()
        
        print("\nContexto del template:")
        print("=" * 40)
        if 'empresa' in context:
            empresa = context['empresa']
            print(f"✅ Variable 'empresa' disponible: {empresa.nombre_taller}")
            print(f"✅ País de la empresa: {empresa.pais}")
        else:
            print("❌ Variable 'empresa' NO disponible en el contexto")
        
        # Verificar formulario
        form_kwargs = view.get_form_kwargs()
        if 'empresa' in form_kwargs:
            print(f"✅ Empresa pasada al formulario: {form_kwargs['empresa'].nombre_taller}")
        else:
            print("❌ Empresa NO pasada al formulario")
        
        # Probar formulario
        from taller.clientes.forms import ClienteForm
        form = ClienteForm(empresa=user_cl.empresa)
        print(f"\nPaís del formulario: {form.pais}")
        
        # Verificar visibilidad de campos
        for field_name in ['region', 'ciudad', 'estado_usa', 'ciudad_usa', 'zipcode']:
            if field_name in form.fields:
                field = form.fields[field_name]
                widget_type = field.widget.__class__.__name__
                es_oculto = widget_type == 'HiddenInput'
                print(f"Campo '{field_name}': {widget_type} - {'OCULTO' if es_oculto else 'VISIBLE'}")
        
    except User.DoesNotExist:
        print("❌ Usuario testuser_cl no encontrado")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()

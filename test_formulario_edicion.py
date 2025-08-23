#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from taller.models.documento import Documento
from taller.models.tecnico import Mecanico
from taller.documentos.forms import DocumentoForm

# Crear cliente de prueba
client = Client()

# Autenticarse con taller2
user = User.objects.filter(username='taller2').first()
if user:
    client.force_login(user)
    print('✅ Autenticado como taller2')
    
    # Obtener el documento 41
    try:
        empresa = user.empresa_usuario
        documento = Documento.objects.get(id=41, empresa=empresa)
        print(f'📄 Documento encontrado: {documento.numero_documento}')
        print(f'📅 Fecha: {documento.fecha}')
        print(f'🔧 Mecánico: {documento.mecanico}')
        
        # Crear formulario con empresa
        form = DocumentoForm(instance=documento, empresa=empresa)
        
        # Verificar campos del formulario
        print(f'\n🎯 Verificando campos del formulario:')
        print(f'   📅 Fecha inicial: {form.initial.get("fecha", "No encontrada")}')
        print(f'   🔧 Mecánico queryset: {form.fields["mecanico"].queryset.count()} mecánicos')
        
        # Listar mecánicos disponibles
        for mecanico in form.fields["mecanico"].queryset:
            print(f'      - {mecanico.nombre} (ID: {mecanico.pk})')
            
        # Verificar si hay mecánicos activos para la empresa
        mecanicos_empresa = Tecnico.objects.filter(empresa=empresa, activo=True)
        print(f'   📊 Mecánicos activos en empresa: {mecanicos_empresa.count()}')
        
        # Probar la vista de edición
        response = client.get(f'/documentos/nuevo-editar/41/')
        print(f'\n📡 Respuesta vista edición: {response.status_code}')
        if response.status_code == 200:
            print('   ✅ Vista carga correctamente')
        else:
            print(f'   ❌ Error: {response.content[:200]}')
            
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
else:
    print('❌ Usuario taller2 no encontrado')

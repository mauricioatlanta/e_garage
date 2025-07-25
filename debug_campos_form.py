#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from django.test import RequestFactory, Client
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from taller.models.documento import Documento, RepuestoDocumento, ServicioDocumento
from taller.documentos.forms import DocumentoForm

# Crear request factory
factory = RequestFactory()
client = Client()

# Autenticarse con taller2
user = User.objects.filter(username='taller2').first()
if user:
    print('✅ Autenticado como taller2')
    
    try:
        # Obtener empresa y documento
        empresa = user.empresa_usuario
        documento = Documento.objects.get(id=41, empresa=empresa)
        
        # Crear formulario
        form = DocumentoForm(instance=documento, empresa=empresa)
        
        # Obtener repuestos y servicios
        repuestos = RepuestoDocumento.objects.filter(documento=documento)
        servicios = ServicioDocumento.objects.filter(documento=documento)
        
        # Calcular totales
        subtotal_repuestos = sum(rep.total for rep in repuestos)
        subtotal_servicios = sum(serv.precio for serv in servicios)
        subtotal = subtotal_repuestos + subtotal_servicios
        iva = int(subtotal * 0.19)
        total = subtotal + iva
        
        # Contexto
        context = {
            'form': form,
            'documento': documento,
            'repuestos': repuestos,
            'servicios': servicios,
            'subtotal_repuestos': subtotal_repuestos,
            'subtotal_servicios': subtotal_servicios,
            'subtotal': subtotal,
            'iva': iva,
            'total': total,
            'editando': True,
        }
        
        # Información de debug
        print(f'📄 Documento: {documento.numero_documento}')
        print(f'📅 Fecha en documento: {documento.fecha}')
        print(f'📅 Fecha en form.initial: {form.initial.get("fecha", "No encontrada")}')
        print(f'📅 Fecha en form bound value: {form["fecha"].value()}')
        print(f'🔧 Mecánico en documento: {documento.mecanico}')
        print(f'🔧 Mecánico en form bound value: {form["mecanico"].value()}')
        print(f'🔧 Mecánicos disponibles: {form.fields["mecanico"].queryset.count()}')
        
        # Verificar si los campos tienen valores
        fecha_field = form["fecha"]
        mecanico_field = form["mecanico"]
        
        print(f'\\n🎯 Análisis de campos:')
        print(f'   📅 Campo fecha:')
        print(f'      - Valor: {fecha_field.value()}')
        print(f'      - HTML: {str(fecha_field)[:100]}...')
        print(f'   🔧 Campo mecánico:')
        print(f'      - Valor: {mecanico_field.value()}')
        print(f'      - HTML: {str(mecanico_field)[:200]}...')
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
else:
    print('❌ Usuario taller2 no encontrado')

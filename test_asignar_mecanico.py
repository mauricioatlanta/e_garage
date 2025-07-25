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
from taller.models.mecanico import Mecanico

# Crear cliente de prueba
client = Client()

# Autenticarse con taller2
user = User.objects.filter(username='taller2').first()
if user:
    client.force_login(user)
    print('✅ Autenticado como taller2')
    
    try:
        # Obtener empresa y documento
        empresa = user.empresa_usuario
        documento = Documento.objects.get(id=41, empresa=empresa)
        mecanicos = Mecanico.objects.filter(empresa=empresa, activo=True)
        
        print(f'📄 Documento: {documento.numero_documento}')
        print(f'📅 Fecha actual: {documento.fecha}')
        print(f'🔧 Mecánico actual: {documento.mecanico}')
        print(f'\\n🔧 Mecánicos disponibles:')
        for m in mecanicos:
            print(f'   - {m.nombre} (ID: {m.pk})')
            
        if mecanicos.exists():
            # Asignar el primer mecánico disponible para test
            primer_mecanico = mecanicos.first()
            documento.mecanico = primer_mecanico
            documento.save()
            
            print(f'\\n✅ Mecánico asignado: {primer_mecanico.nombre}')
            print(f'✅ Documento actualizado: {documento.mecanico}')
            
            # Verificar que se guardó correctamente
            documento_updated = Documento.objects.get(id=41, empresa=empresa)
            print(f'✅ Verificación - mecánico guardado: {documento_updated.mecanico}')
            
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
else:
    print('❌ Usuario taller2 no encontrado')

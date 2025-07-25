#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gestion_taller.settings')
django.setup()

from taller.models.documento import Documento
from django.contrib.auth.models import User

user = User.objects.filter(username='taller2').first()
if user:
    try:
        empresa = user.empresa_usuario
        
        # Listar documentos de la empresa para ver qué IDs existen
        documentos = Documento.objects.filter(empresa=empresa).order_by('-id')[:10]
        print(f'📄 Últimos 10 documentos de {empresa.nombre_taller}:')
        for doc in documentos:
            print(f'   ID: {doc.id} - {doc.numero_documento} ({doc.tipo_documento}) - {doc.fecha}')
            
        # Buscar documento 107 específicamente
        try:
            doc107 = Documento.objects.get(id=107, empresa=empresa)
            print(f'\n✅ Documento 107 encontrado: {doc107.numero_documento}')
        except Documento.DoesNotExist:
            print(f'\n❌ Documento 107 no existe para {empresa.nombre_taller}')
            
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
else:
    print('❌ Usuario taller2 no encontrado')
